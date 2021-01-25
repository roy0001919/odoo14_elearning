# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date, time
import pytz
from dateutil import rrule
import logging
import hashlib
import base64
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import ValidationError
import qrcode
import StringIO

_logger = logging.getLogger(__name__)

slot_quo_cache = {}
# global slot_qty_cache
# slot_qty_cache = {}


class CalendarSlot(models.Model):
    _name = 'booking_calendar.slot'

    slot_start = fields.Datetime()
    qty = fields.Integer()

    @api.multi
    def count_slot_qty(self, booking_start):
        tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        lines = self.env['sale.order.line'].sudo().search(
            [('booking_start', '=', booking_start), ('active', '=', True), ('state', 'in', ['sale', 'sent', 'draft'])])
        qty = sum(line.product_uom_qty for line in lines)
        today = datetime.strftime(datetime.now().replace(tzinfo=pytz.utc).astimezone(tz), '%Y-%m-%d 00:00:00')
        slot = self.env['booking_calendar.slot'].sudo().search(['|', ('slot_start', '=', booking_start), ('slot_start', '<=', today)])
        for s in slot:
            s.unlink()
        self.env['booking_calendar.slot'].sudo().create({'slot_start': booking_start, 'qty': qty})
        return qty


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    calendar_id = fields.Many2one('resource.calendar', string='Working time')
    capacity = fields.Integer(string='Number of Products')
    pay_online = fields.Boolean(string='Pay Online', default=True)
    resource_ids = fields.Many2many('resource.resource', 'product_resource_rel', string='Related Resource')
    min_order = fields.Integer(string='Minimum Order Quantity')
    max_order = fields.Integer(string='Maximum Order Quantity')
    html_color = fields.Char('Color')


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    to_calendar = fields.Boolean('Display on calendar')
    color = fields.Char('Color')
    has_slot_calendar = fields.Boolean('Use Working Time as Slots Definition')
    duration_mins = fields.Integer('Duration (minutes)', default=30)
    reserve_days = fields.Integer('Reserve Days', default=30)
    product_ids = fields.Many2many('product.template', 'product_resource_rel', string='Related Products')

    start_delay_unit = fields.Selection([('min', 'Minute'), ('day', 'Day')], 'Start Delay Unit', default='min')
    slot_start_delay = fields.Integer('Slot Start Delay', default=0)
    refundable_days = fields.Integer('Refundable Days', default=0)


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    website_quota = fields.Integer('Website Quota')
    pos_quota = fields.Integer('POS Quota')

    @api.multi
    def write(self, vals):
        result = super(ResourceCalendarAttendance, self).write(vals)
        slot_quo_cache.clear()
        return result


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    @api.multi
    def get_working_accurate_hours(self, start_dt=None, end_dt=None):
        """
            Replacement of resource calendar method get_working_hours
            Allows to handle hour_to = 00:00
            Takes in account minutes
            Adds public holidays time (resource leaves with reason = PH)
        """
        leave_obj = self.env['resource.calendar.leaves']
        for calendar in self:
            id = calendar.id
            hours = timedelta()
            for day in rrule.rrule(rrule.DAILY, dtstart=start_dt,
                                   until=end_dt.replace(hour=23, minute=59, second=59),
                                   byweekday=calendar.get_weekdays()[0]):
                day_start_dt = day.replace(hour=0, minute=0, second=0)
                if start_dt and day.date() == start_dt.date():
                    day_start_dt = start_dt
                day_end_dt = day.replace(hour=23, minute=59, second=59)
                if end_dt and day.date() == end_dt.date():
                    day_end_dt = end_dt
                work_limits = []
                work_limits.append((day_start_dt.replace(hour=0, minute=0, second=0), day_start_dt))
                work_limits.append((day_end_dt, day_end_dt.replace(hour=23, minute=59, second=59)))

                intervals = []
                work_dt = day_start_dt.replace(hour=0, minute=0, second=0)
                working_intervals = []
                for calendar_working_day in calendar.get_attendances_for_weekday(day_start_dt)[0]:
                    min_from = int((calendar_working_day.hour_from - int(calendar_working_day.hour_from)) * 60)
                    min_to = int((calendar_working_day.hour_to - int(calendar_working_day.hour_to)) * 60)
                    x = work_dt.replace(hour=int(calendar_working_day.hour_from), minute=min_from)
                    if calendar_working_day.hour_to == 0:
                        y = work_dt.replace(hour=0, minute=0) + timedelta(days=1)
                    else:
                        y = work_dt.replace(hour=int(calendar_working_day.hour_to), minute=min_to)
                    working_interval = (x, y)
                    working_intervals += calendar.interval_remove_leaves(working_interval, work_limits)
                for interval in working_intervals:
                    hours += interval[1] - interval[0]

            # Add public holidays
            leaves = leave_obj.search([('name', '=', 'PH'), ('calendar_id', '=', calendar.id)])
            leave_intervals = []
            for l in leaves:
                leave_intervals.append((datetime.strptime(l.date_from, DTF),
                                        datetime.strptime(l.date_to, DTF)
                                        ))
            clean_intervals = calendar.interval_remove_leaves((start_dt, end_dt), leave_intervals)

            for interval in clean_intervals:
                hours += (end_dt - start_dt) - (interval[1] - interval[0])

        return seconds(hours) / 3600.0

    @api.multi
    def validate_time_limits(self, booking_start, booking_end):
        # localize UTC dates to be able to compare with hours in Working Time
        # tz_offset = self.env.context.get('tz_offset')
        # if tz_offset:
        # 	start_dt = datetime.strptime(booking_start, DTF) - timedelta(minutes=tz_offset)
        # 	end_dt = datetime.strptime(booking_end, DTF) - timedelta(minutes=tz_offset)
        # else:
        # 	user_tz = pytz.timezone(self.env.context.get('tz') or 'UTC')
        # 	start_dt = pytz.utc.localize(fields.Datetime.from_string(booking_start)).astimezone(user_tz)
        # 	end_dt = pytz.utc.localize(fields.Datetime.from_string(booking_end)).astimezone(user_tz)
        # for calendar in self:
        # 	hours = calendar.get_working_accurate_hours(start_dt, end_dt)
        # 	duration = seconds(end_dt - start_dt) / 3600.0
        # 	if round(hours, 2) != round(duration, 2):
        # 		return False
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'booking_start desc, order_id, id, layout_category_id, sequence'

    resource_id = fields.Many2one('resource.resource', 'Resource')
    # slot_quota = fields.Integer(compute='_compute_slot_quota', store=False, string='Quota')
    slot_quantity = fields.Integer(compute='_compute_slot_quantity', store=False, string='Total Quantity')
    booking_start = fields.Datetime(string="Date start")
    checkin_time = fields.Datetime(string="Checkin Time")
    booking_end = fields.Datetime(string="Date end")
    booking_batch = fields.Integer(string="Batch")
    batch_info = fields.Char(compute='_compute_batch_info', string="Batch Information")
    calendar_id = fields.Many2one('resource.calendar', related='product_id.calendar_id')
    project_id = fields.Many2one('account.analytic.account', related='order_id.project_id', store=False,
                                 string='Contract')
    partner_id = fields.Many2one('res.partner', related='order_id.partner_id', store=False, string='Customer')
    overlap = fields.Boolean(compute='_compute_date_overlap', default=False, store=True)
    automatic = fields.Boolean(default=False, store=True, help='automatically generated booking lines')
    active = fields.Boolean(default=True)
    ticket = fields.Char(compute='_compute_ticket', string='Ticket Number', store=True)
    resource_trigger = fields.Integer(help='''we use this feild in _compute_date_overlap instead of resource_id
    because resource_id is related to pitch in pitch_booking module. If we hadn't done it then _compute_date_overlap would be called
    for each line with the same resource instead of only only for current new line''')

    product_name = fields.Char(compute='_compute_product_name_defalut', store=True)
    product_cate = fields.Char(compute='_compute_product_cate_defalut', store=True)
    product_entry = fields.Char(compute='_compute_product_entry_defalut', store=True)
    ticket_qr = fields.Text(compute='_compute_qr_by_ticket')
    ticket_img = fields.Binary(compute='_compute_qr_img_by_ticket')
    origin = fields.Char(related='order_id.origin')

    note = fields.Text(related='order_id.note')

    buyer = fields.Char(string='Buyer', related='partner_id.name', store=True)
    buyer_tel = fields.Char(string='Buyer Tel', related='partner_id.phone', store=True)
    contact_usr = fields.Char(string='Contact User')
    contact_tel = fields.Char(string='Contact Tel')

    remark1 = fields.Char(string='Remark 1')
    remark2 = fields.Char(string='Remark 2')
    remark3 = fields.Char(string='Remark 3')

    ref_ticket = fields.Char(related='order_id.ref_ticket')

    team_id = fields.Many2one(related='order_id.team_id', store=True)
    ticket_name = fields.Char(compute='_compute_ticket_name', store=True)

    @api.multi
    @api.depends('team_id', 'order_id.name')
    def _compute_ticket_name(self):
        for l in self:
            if l.team_id.id == 1:
                l.ticket_name = l.order_id.name.replace('S', 'K')
            else:
                l.ticket_name = l.order_id.name

    @api.depends('ticket')
    def _compute_qr_img_by_ticket(self):
        for rec in self:
            rec.ticket_img = qrcode.make(rec.ticket)
        # qr = qrcode.QRCode(
        # 	version=5,
        # 	error_correction=qrcode.constants.ERROR_CORRECT_M,
        # 	box_size=10,
        # 	border=4,
        # )
        # for rec in self:
        # 	qr.add_data(rec.ticket)
        # 	qr.make(fit=True)
        # 	img = qr.make_image()
        # 	output = StringIO.StringIO()
        # 	img.save(output, 'PNG')
        # 	contents = output.getvalue()
        # 	rec.ticket_img = base64.b64encode(contents)

    @api.depends('ticket')
    def _compute_qr_by_ticket(self):
        for rec in self:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(rec.ticket)
            qr.make(fit=True)
            img = qr.make_image()
            output = StringIO.StringIO()
            img.save(output, 'PNG')
            contents = output.getvalue()
            data = base64.b64encode(contents)
            rec.ticket_qr = "data:image/png;base64,%s" % data
            # _logger.info('QRCODE: %s' % rec.ticket_qr)
            output.close()

    @api.depends('product_id')
    def _compute_product_name_defalut(self):
        for rec in self:
            if rec.product_id:
                rec.product_name = rec.product_id.with_context({'lang': 'zh_TW'}).name

    @api.depends('product_id')
    def _compute_product_cate_defalut(self):
        for rec in self:
            if rec.product_id.attribute_value_ids:
                if rec.product_id.attribute_value_ids[0]:
                    rec.product_cate = rec.product_id.attribute_value_ids[0].with_context({'lang': 'zh_TW'}).name

    @api.depends('product_id')
    def _compute_product_entry_defalut(self):
        for rec in self:
            if rec.product_id.attribute_value_ids:
                if len(rec.product_id.attribute_value_ids) >= 2:
                    if rec.product_id.attribute_value_ids[1]:
                        rec.product_entry = rec.product_id.attribute_value_ids[1].with_context({'lang': 'zh_TW'}).name

    @api.multi
    def write(self, vals):
        result = super(SaleOrderLine, self).write(vals)
        if vals.get('resource_id'):
            vals['resource_trigger'] = vals.get('resource_id')
        # slot_qty_cache.pop(self.booking_start, None)

        self.env['booking_calendar.slot'].count_slot_qty(self.booking_start)
        return result

    @api.multi
    @api.depends('order_id.name', 'price_total')
    def _compute_ticket(self):
        for rec in self:
            code = "%s%dLiouLiBizNavi@CENOQBridge%s" % (rec.order_id.name, rec.id, rec.batch_info)
            rec.ticket = hashlib.sha512(code).hexdigest()

            if rec.remark3 is not False and rec.remark3 != '':
                rec.ticket = rec.remark3

    @api.multi
    def _compute_batch_info(self):
        tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        for rec in self:
            if rec.booking_batch:
                batch = _("Batch [ %d ]") % rec.booking_batch
                if datetime.strptime(rec.booking_start, DTF).date() == datetime.strptime(rec.booking_end, DTF).date():
                    rec.batch_info = '%s~%s %s' % (
                        datetime.strftime(
                            datetime.strptime(rec.booking_start, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
                            '%Y/%m/%d %H:%M'),
                        datetime.strftime(
                            datetime.strptime(rec.booking_end, DTF).replace(tzinfo=pytz.utc).astimezone(tz), '%H:%M'),
                        batch)
                else:
                    rec.batch_info = '%s~%s %s' % (
                        datetime.strftime(
                            datetime.strptime(rec.booking_start, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
                            '%Y/%m/%d %H:%M'),
                        datetime.strftime(
                            datetime.strptime(rec.booking_end, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
                            '%Y/%m/%d %H:%M'), batch)

    @api.multi
    def get_self_slot_qty(self):
        for line in self:
            return line.get_slot_qty(line.booking_start)

    @api.multi
    def get_slot_remain_qty(self):
        tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        for line in self:
            start = datetime.strptime(line.booking_start, DTF).replace(tzinfo=pytz.utc).astimezone(tz)
            quo = slot_quo_cache.get(datetime(start.year, start.month, start.day, start.hour, start.minute)) or 250

            return quo - line.get_slot_qty(line.booking_start)

    @api.multi
    def get_slot_qty(self, booking_start):
        slot = self.env['booking_calendar.slot'].sudo().search([('slot_start', '=', booking_start)], limit=1)
        if not slot:
            lines = self.env['sale.order.line'].sudo().search(
                [('booking_start', '=', booking_start), ('active', '=', True), ('state', 'in', ['sale', 'sent', 'draft'])])
            qty = sum(line.product_uom_qty for line in lines)
            slot = self.env['booking_calendar.slot'].create({'slot_start': booking_start, 'qty': qty})
        return slot.qty

    @api.multi
    def _compute_slot_quantity(self):
        for rec in self:
            rec.slot_quantity = self.get_slot_qty(rec.booking_start)
            # if slot_qty_cache.get(rec.booking_start):
            #     # and datetime.now() < (slot_qty_cache.get(rec.booking_start)[0] + timedelta(minutes=60)):
            #     rec.slot_quantity = slot_qty_cache.get(rec.booking_start)[1]
            # else:
            #     lines = rec.env['sale.order.line'].sudo().search(
            #         [('booking_start', '=', rec.booking_start), ('active', '=', True), ('state', 'in', ['sale', 'sent', 'draft'])])
            #     # resource_products = [p.id for p in rec.product_id.resource_ids[0].product_ids]
            #     # lines = rec.env['sale.order.line'].sudo().search(
            #     #     [('booking_start', '=', rec.booking_start), ('active', '=', True), ('state', '!=', 'cancel'),
            #     #      ('product_id.product_tmpl_id', 'in', resource_products)])
            #     # print resource_products
            #     rec.slot_quantity = sum(line.product_uom_qty for line in lines)
            #     slot_qty_cache.setdefault(rec.booking_start, [datetime.now(), rec.slot_quantity])

    # @api.multi
    # def _compute_slot_quota(self):
    #     for rec in self:
    #         print rec.booking_start
    #         # if slot_quo_cache.get(rec.booking_start) and slot_quo_cache.get(rec.booking_start) > 0:
    #             # and datetime.now() > (slot_qty_cache.get(rec.booking_start)[0] + timedelta(minutes=1)):
    #         print slot_quo_cache
    #         rec.slot_quota = slot_quo_cache.get(rec.booking_start)
    # else:
    #     rec.slot_quota = rec.product_id.capacity

    @api.multi
    @api.depends('resource_trigger', 'booking_start', 'booking_end', 'active')
    def _compute_date_overlap(self):
        for line in self:
            line.overlap = False
        # if not line.active:
        # 	line.overlap = False
        # 	continue
        # overlaps = 0
        # if line.resource_id and line.booking_start and line.booking_end:
        # 	ids = getattr(self, '_origin', False) and self._origin.ids or bool(line.id) and [line.id] or []
        # 	overlaps = line.search_count([('active', '=', True),
        # 								  '&', '|', '&', ('booking_start', '>=', line.booking_start), ('booking_start', '<', line.booking_end),
        # 								  '&', ('booking_end', '>', line.booking_start), ('booking_end', '<=', line.booking_end),
        # 								  ('resource_id', '!=', False),
        # 								  ('id', 'not in', ids),
        # 								  ('resource_id', '=', line.resource_id.id),
        # 								  ('state', '!=', 'cancel')])
        # 	overlaps += line.search_count([('active', '=', True),
        # 								   ('id', 'not in', ids),
        # 								   ('booking_start', '=', line.booking_start),
        # 								   ('booking_end', '=', line.booking_end),
        # 								   ('resource_id', '=', line.resource_id.id),
        # 								   ('state', '!=', 'cancel')])
        # line.overlap = bool(overlaps)

    @api.multi
    @api.constrains('overlap')
    def _check_overlap(self):
        for line in self:
            if line.overlap:
                overlaps_with = self.search([('active', '=', True),
                                             '&', '|', '&', ('booking_start', '>', line.booking_start),
                                             ('booking_start', '<', line.booking_end),
                                             '&', ('booking_end', '>', line.booking_start),
                                             ('booking_end', '<', line.booking_end),
                                             ('resource_id', '!=', False),
                                             ('id', '!=', line.id),
                                             ('resource_id', '=', line.resource_id.id),
                                             ('state', '!=', 'cancel')])
                overlaps_with += self.search([('active', '=', True),
                                              ('id', '!=', line.id),
                                              ('booking_start', '=', line.booking_start),
                                              ('booking_end', '=', line.booking_end),
                                              ('resource_id', '=', line.resource_id.id),
                                              ('state', '!=', 'cancel')])

                msg = 'There are bookings with overlapping times: %(this)s and %(those)s' % {'this': [line.id],
                                                                                             'those': overlaps_with.ids}
                raise ValidationError(msg)

    @api.multi
    @api.constrains('calendar_id', 'booking_start', 'booking_end')
    def _check_date_fit_product_calendar(self):
        for line in self.sudo():
            if line.state == 'cancel':
                continue
            if line.calendar_id and line.booking_start and line.booking_end:
                if not line.calendar_id.validate_time_limits(line.booking_start, line.booking_end):
                    raise ValidationError(_('Not valid interval of booking for the product %s.') % line.product_id.name)

    @api.multi
    @api.constrains('resource_trigger', 'booking_start', 'booking_end')
    def _check_date_fit_resource_calendar(self):
        for line in self.sudo():
            if line.state == 'cancel':
                continue
            if line.resource_id and line.resource_id.calendar_id and line.booking_start and line.booking_end:
                if not line.resource_id.calendar_id.validate_time_limits(line.booking_start, line.booking_end):
                    raise ValidationError(
                        _('Not valid interval of booking for the resource %s.') % line.resource_id.name)

    @api.multi
    @api.constrains('booking_start')
    def _check_booking_start(self):
        for line in self:
            if not line.booking_start:
                continue
            if line.resource_id.start_delay_unit == 'day':
                if datetime.strptime(line.booking_start, DTF) - timedelta(
                        days=line.resource_id.slot_start_delay) <= datetime.combine(date.today(), datetime.min.time()):
                    # raise ValidationError(_('Please book on time in %s days from now.') % SLOT_START_DELAY_DAYS)
                    return False
            else:
                if datetime.strptime(line.booking_start, DTF) - timedelta(
                        minutes=line.resource_id.slot_start_delay) <= datetime.now():
                    # raise ValidationError(_('Please book on time in %s minutes from now.') % SLOT_START_DELAY_MINS)
                    return False

    @api.model
    def search_booking_lines(self, start, end, domain):
        domain.append(('state', 'in', ['sale', 'sent', 'draft']))
        domain.append(('booking_end', '>=', fields.Datetime.now()))
        domain.append('|')
        domain.append('|')
        domain.append('&')
        domain.append(('booking_start', '>=', start))
        domain.append(('booking_start', '<', end))
        domain.append('&')
        domain.append(('booking_end', '>', start))
        domain.append(('booking_end', '<=', end))
        domain.append('&')
        domain.append(('booking_start', '<=', start))
        domain.append(('booking_end', '>=', end))
        return self.search(domain)

    @api.model
    def get_bookings(self, start, end, offset, domain):
        bookings = self.sudo().search_booking_lines(start, end, domain)
        res = []
        for b in bookings:
            if b.slot_quantity >= slot_quo_cache.get(start):
                res.append({
                    'className': 'booked_slot resource_%s' % b.resource_id.id,
                    'id': b.id,
                    # 'title': b.resource_id.name,
                    'title': 'Full',
                    'start': '%s+00:00' % b.booking_start,
                    'end': '%s+00:00' % b.booking_end,
                    'resource_id': b.resource_id.id,
                    'editable': False,
                    'color': b.resource_id.color
                })
        return res

    # @api.onchange('booking_start', 'booking_end')
    # def _on_change_booking_time(self):
    #     domain = {'product_id': []}
    #     # if self.venue_id:
    #     #     domain['product_id'].append(('venue_id', '=', self.venue_id.id))
    #     if self.booking_start and self.booking_end:
    #         start = datetime.strptime(self.booking_start, DTF)
    #         end = datetime.strptime(self.booking_end, DTF)
    #         self.product_uom_qty = (end - start).seconds / 3600
    #         booking_products = self.env['product.product'].search([('calendar_id', '!=', False)])
    #         domain_products = []
    #         domain_products = [p.id for p in booking_products
    #                            if p.calendar_id.validate_time_limits(self.booking_start, self.booking_end)]
    #         if domain_products:
    #             domain['product_id'].append(('id', 'in', domain_products))
    #     return {'domain': domain}

    # @api.onchange('partner_id', 'project_id')
    # def _on_change_partner(self):
    #     if self.order_id and self.order_id.partner_id != self.partner_id:
    #         self.order_id = None
    #     if self.order_id and self.order_id.project_id != self.project_id:
    #         self.order_id = None
    #     return self.env['sale.order'].browse().onchange_partner_id(self.partner_id.id)

    @api.onchange('order_id')
    def _on_change_order(self):
        if self.order_id:
            self.partner_id = self.order_id.partner_id
            self.project_id = self.order_id.project_id

    @api.model
    def read_color(self, color_field):
        return self.env['resource.resource'].sudo().browse(color_field).color

    @api.model
    def create(self, values):
        if not values.get('order_id') and values.get('partner_id'):
            order = self.env['sale.order'].sudo().create({'partner_id': values.get('partner_id')})
            order.onchange_partner_id()
            values.update({'order_id': order.id})
        return super(SaleOrderLine, self).create(values)

    @api.onchange('product_id')
    def _on_change_product_id(self):
        if self.product_id:
            name = self.product_id.name_get()[0][1]
            self.price_unit = self.product_id.list_price
            resources = self.env['resource.resource'].sudo().search(
                [('calendar_id', '=', self.product_id.calendar_id.id)])
            if len(resources) > 0:
                self.resource_id = resources[0]
                if self.product_id.description_sale:
                    name += '\n' + self.product_id.description_sale
                self.name = name
                warning = {}
                if self.product_id.sale_line_warn != 'no-message':
                    title = _("Warning for %s") % self.product_id.name
                    message = self.product_id.sale_line_warn_msg
                    warning['title'] = title
                    warning['message'] = message
                    if self.product_id.sale_line_warn == 'block':
                        return {'value': {'product_id': False}, 'warning': warning}
                    else:
                        return {'warning': warning}

    @api.onchange('product_id', 'partner_id', 'product_uom_qty')
    def _on_change_product_partner_id(self):
        if self.product_id and self.partner_id:
            pricelist = self.partner_id.property_product_pricelist
            if pricelist:
                data = self.product_id_change()
            # for k in data['value']:
            #     if not k in ['name']:
            #         setattr(self, k, data['value'][k])

    @api.model
    def get_resources(self, venue_id, pitch_id):
        pitch_obj = self.env['pitch_booking.pitch'].sudo()
        venue_obj = self.env['pitch_booking.venue'].sudo()
        if not venue_id:
            venues = venue_obj.search([])
            venue_id = venues[0].id if venues else None
        resources = []
        if pitch_id:
            resources = [pitch_obj.browse(int(pitch_id)).resource_id]
        elif venue_id:
            resources = [p.resource_id for p in pitch_obj.search([('venue_id', '=', int(venue_id))])]
        return [{
            'name': r.name,
            'id': r.id,
            'color': r.color
        } for r in resources]

    @api.model
    def generate_slot(self, r, start_dt, end_dt, title, batch):
        if not title:
            title = r.name
        if batch:
            title = _('Batch [ %s ] %s') % (batch, title)
        return {
            'start': start_dt.strftime(DTF),
            'end': end_dt.strftime(DTF),
            'title': title,
            'batch': batch,
            'color': r.color,
            'className': 'free_slot resource_%s' % r.id,
            'editable': False,
            'resource_id': r.id
        }

    # @staticmethod
    # def capacity_adjust(start_dt, end_dt, product_id):
    #     print start_dt
    #     return product_id.capacity

    @api.model
    def del_booked_slots(self, slots, start, end, resources, offset, fixed_start_dt, end_dt):
        for r in resources:
            if r.start_delay_unit == 'day':
                now = datetime.now() + timedelta(days=r.slot_start_delay) - timedelta(
                    minutes=offset)
                now = datetime.strptime(datetime.strftime(now, '%Y-%m-%d 00:00:00'), DTF)
            else:
                now = datetime.now() + timedelta(minutes=r.slot_start_delay) - timedelta(
                    minutes=offset)

            lines = self.search_booking_lines(start, end, [])
            slot_arr = []
            for l in lines:
                line_start_dt = datetime.strptime(l.booking_start, '%Y-%m-%d %H:%M:%S') - timedelta(minutes=offset)
                # line_start_dt -= timedelta(minutes=divmod(line_start_dt.minute, r.duration_mins)[1])
                line_end_dt = datetime.strptime(l.booking_end, DTF) - timedelta(minutes=offset)
                while line_start_dt < line_end_dt:
                    if line_start_dt not in slot_arr:
                        slot_arr.append(line_start_dt)
                        if line_start_dt >= end_dt + timedelta(days=1):
                            break
                        elif line_start_dt < fixed_start_dt or line_start_dt < now:
                            line_start_dt += timedelta(minutes=r.duration_mins)
                            continue
                        try:
                            qty = l.slot_quantity
                            remain = slot_quo_cache.get(line_start_dt) - qty
                            # remain = self.capacity_adjust(line_start_dt, line_end_dt, l.product_id) - qty
                            batch = slots[l.resource_id.id][line_start_dt.strftime(DTF)].get('batch')
                            if remain <= 0:
                                # del slots[l.resource_id.id][line_start_dt.strftime(DTF)]
                                slots[l.resource_id.id][line_start_dt.strftime(DTF)]['title'] = _(
                                    'Batch [ %d ] %s ~ %s (Full)') % (batch,
                                                                      line_start_dt.strftime("%H:%M"),
                                                                      line_end_dt.strftime("%H:%M"))
                            else:
                                slots[l.resource_id.id][line_start_dt.strftime(DTF)]['title'] = _(
                                    'Batch [ %d ] %s ~ %s (left %d)') % (batch,
                                                                         line_start_dt.strftime("%H:%M"),
                                                                         line_end_dt.strftime("%H:%M"), remain)
                        except:
                            pass
                            # _logger.warning('cannot free slot %s %s' % (
                            #     l.resource_id.id,
                            #     line_start_dt.strftime(DTF)
                            # ))
                    line_start_dt += timedelta(minutes=r.duration_mins)

        leave_slot_dts = []
        now = datetime.strptime(datetime.strftime(now, '%Y-%m-%d 00:00:00'), DTF)
        for r in resources:
            leaves = self.env['resource.calendar.leaves'].search(
                [('date_to', '>', datetime.strftime(now, DTF)), ('calendar_id', '=', r.calendar_id.id)])
            for slot_time in slots[r.id]:
                for leave in leaves:
                    from_dt = datetime.strptime(leave.date_from, '%Y-%m-%d %H:%M:%S') - timedelta(minutes=offset)
                    to_dt = datetime.strptime(leave.date_to, '%Y-%m-%d %H:%M:%S') - timedelta(minutes=offset)
                    slot_dt = datetime.strptime(slot_time, '%Y-%m-%d %H:%M:%S')
                    if from_dt <= slot_dt and to_dt > slot_dt:
                        leave_slot_dts.append(slot_dt.strftime(DTF))

        for slot_dt in leave_slot_dts:
            del slots[r.id][slot_dt]

        return slots

    @api.model
    def get_free_slots_resources(self, domain):
        product_id = domain[0].get('product_id')
        resources = self.env['resource.resource'].sudo().search(
            [('to_calendar', '=', True), ('product_ids', '=', product_id)])
        return resources

    @api.model
    def get_free_slots(self, start, end, offset, domain):
        leave_obj = self.env['resource.calendar.leaves'].sudo()
        tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        now = datetime.utcnow()
        start_dt = datetime.strptime(start, DTF) - timedelta(minutes=offset)
        end_dt = datetime.strptime(end, DTF) - timedelta(minutes=offset)
        fixed_start_dt = start_dt
        resources = self.get_free_slots_resources(domain)
        slots = {}
        # now = datetime.strptime(datetime.strftime(now, '%Y-%m-%d 00:00:00'), DTF)
        for r in resources:
            if r.start_delay_unit == 'day':
                now = datetime.now() + timedelta(days=r.slot_start_delay) - timedelta(
                    minutes=offset)
                now = datetime.strptime(datetime.strftime(now, '%Y-%m-%d 00:00:00'), DTF)
            else:
                now = datetime.now() + timedelta(minutes=r.slot_start_delay) - timedelta(
                    minutes=offset)

            reserve_dt = now + timedelta(days=r.reserve_days)
            if r.reserve_days > 0 and reserve_dt <= end_dt:
                end_dt = reserve_dt
            if r.id not in slots:
                slots[r.id] = {}
            start_dt = fixed_start_dt
            curr_day = start_dt.strftime("%Y-%m-%d")
            batch = 0
            while start_dt <= end_dt:
                if (r.start_delay_unit == 'day' and start_dt.date() <= now.date()) or (
                        not r.start_delay_unit == 'day' and tz.localize(start_dt) <= tz.localize(now)):
                    start_dt += timedelta(minutes=r.duration_mins)
                    continue
                if r.calendar_id:
                    for calendar_working_day in r.calendar_id.get_attendances_for_weekday(start_dt):
                        min_from = int((calendar_working_day.hour_from - int(calendar_working_day.hour_from)) * 60)
                        min_to = int((calendar_working_day.hour_to - int(calendar_working_day.hour_to)) * 60)
                        x = start_dt.replace(hour=int(calendar_working_day.hour_from), minute=min_from)
                        if calendar_working_day.hour_to == 0:
                            y = start_dt.replace(hour=0, minute=0) + timedelta(days=1)
                        else:
                            y = start_dt.replace(hour=int(calendar_working_day.hour_to), minute=min_to)
                        if r.has_slot_calendar and x >= now and x >= start_dt and y <= end_dt:
                            slots[r.id][x.strftime(DTF)] = self.generate_slot(r, x, y, None, None)
                        elif not r.has_slot_calendar:
                            if x.strftime("%Y-%m-%d") != curr_day:
                                curr_day = x.strftime("%Y-%m-%d")
                                batch = 0
                            while x < y:
                                if not slots[r.id].get(x.strftime(DTF)):
                                    batch += 1
                                if x >= now:
                                    if calendar_working_day.website_quota > 0:
                                        slot_quo_cache.setdefault(x, calendar_working_day.website_quota)
                                    else:
                                        slot_quo_cache.setdefault(x, r.product_ids[0].capacity)
                                    if not slots[r.id].get(x.strftime(DTF)):
                                        if tz.localize(x) > datetime.now(tz):
                                            # _logger.info("product: %s" % r.products[0].capacity)
                                            # _logger.info("start date: %s" % self.capacity_adjust(x, (x + timedelta(minutes=r.duration_mins)), r.products[0].capacity))
                                            title = _('%s ~ %s (left %d)') % (x.strftime("%H:%M"), (
                                                    x + timedelta(minutes=r.duration_mins)).strftime("%H:%M"),
                                                                              slot_quo_cache.get(x))
                                            # self.capacity_adjust(x, (x + timedelta(minutes=r.duration_mins)), r.product_ids[0]))
                                            slots[r.id][x.strftime(DTF)] = self.generate_slot(r, x, x + timedelta(
                                                minutes=r.duration_mins), title, batch)
                                x += timedelta(minutes=r.duration_mins)
                    start_dt += timedelta(days=1)
                    start_dt = start_dt.replace(hour=0, minute=0, second=0)
                else:
                    slots[r.id][start_dt.strftime(DTF)] = self.generate_slot(r, start_dt, start_dt + timedelta(
                        minutes=r.duration_mins), None, None)
                    start_dt += timedelta(minutes=r.duration_mins)
                    continue
            leaves = leave_obj.search([('name', '=', 'PH'), ('calendar_id', '=', r.calendar_id.id)])
            for leave in leaves:
                from_dt = datetime.strptime(leave.date_from, '%Y-%m-%d %H:%M:00') - timedelta(minutes=offset)
                to_dt = datetime.strptime(leave.date_to, '%Y-%m-%d %H:%M:00') - timedelta(minutes=offset)
                if r.has_slot_calendar:
                    if from_dt >= now and from_dt >= start_dt and to_dt <= end_dt:
                        slots[r.id][from_dt.strftime(DTF)] = self.generate_slot(r, from_dt, end_dt, None, None)
                    else:
                        continue
                else:
                    from_dt = max(now, from_dt)
                    while from_dt < to_dt:
                        slots[r.id][from_dt.strftime(DTF)] = self.generate_slot(r, from_dt, from_dt + timedelta(
                            minutes=self.duration_mins), None, None)
                        from_dt += timedelta(minutes=r.duration_mins)

        res = []
        for slot in self.del_booked_slots(slots, start, end, resources, offset, fixed_start_dt, end_dt).values():
            for pitch in slot.values():
                res.append(pitch)
        return res

    @api.multi
    def check_refundable(self):
        for rec in self:
            tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
            today = datetime.now(tz).date()
            if rec.booking_start and rec.order_id.state != 'cancel':
                bd = datetime.strptime(rec.booking_start, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(
                    tz).date()
                return not rec.checkin_time and (bd - today) > timedelta(days=rec.sudo().resource_id.refundable_days)
            else:
                return False

    @api.multi
    def check_bookable(self):
        for rec in self:
            tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
            now = datetime.now(tz)
            if rec.booking_start:
                bd = datetime.strptime(rec.booking_start, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(tz)
                return not rec.checkin_time and (bd - now) > timedelta(minutes=0)
            else:
                return False

    @api.multi
    def action_open_sale_order(self):
        view_id = self.env.ref('sale.view_order_form')
        order_obj = self.env['sale.order'].sudo().search([('id', '=', self.order_id.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Booking',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_id': order_obj.id,
            'res_model': 'sale.order',
            'target': 'current',
        }


# class SaleOrderAmountTotal(models.Model):
#     _inherit = 'sale.order'
#
#     def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
#         return super(SaleOrderAmountTotal, self)._amount_all_wrapper(cr, uid, ids, field_name, arg, context=None)
#
#     def _get_order(self, cr, uid, ids, context=None):
#         result = {}
#         for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
#             result[line.order_id.id] = True
#         return result.keys()
#
#     _columns = {
#         'amount_total': old_api_fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Total',
#                                                 store={
#                                                     'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
#                                                     'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'state'], 10),
#         },
#             multi='sums', help="The total amount."),
#     }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ticket = fields.Char(compute='_compute_ticket', string='Ticket Number')
    ref_ticket = fields.Char(string='Ref Ticket')

    # @api.multi
    # def action_confirm(self):
    #     for order in self:
    #         order.state = 'sale'
    #         order.confirmation_date = fields.Datetime.now()
    #         if self.env.context.get('send_email') and order.state == 'sale':
    #             self.force_quotation_send()
    #         order.order_line._action_procurement_create()
    #     if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
    #         self.action_done()
    #     return True
    @api.multi
    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        for line in self.order_line:
            self.env['booking_calendar.slot'].count_slot_qty(line.booking_start)
            # slot_qty_cache.pop(line.booking_start, None)

        return result

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        # for line in self.order_line:
        #     self.env['booking_calendar.slot'].count_slot_qty(line.booking_start)
            # slot_qty_cache.pop(line.booking_start, None)

        return result

    @api.multi
    def post_action(self):
        public_users = [u.name for u in self.env['res.users'].sudo().search([('active', '=', False)])]
        for order in self:
            for line in order.order_line:
                if (
                        not line.contact_usr or line.contact_usr.strip() == "") and order.partner_id.name not in public_users:
                    line.contact_usr = order.partner_id.name
                if (
                        not line.contact_tel or line.contact_tel.strip() == "") and order.partner_id.name not in public_users:
                    line.contact_tel = order.partner_id.phone

    @api.multi
    def _compute_ticket(self):
        for rec in self:
            code = hashlib.sha512(rec.name + "LiouLiBizNavi@CENOQBridge" + rec.date_order).hexdigest()
            rec.ticket = code

    @api.multi
    def check_refundable(self):
        for rec in self:
            for line in rec.order_line:
                if not line.check_refundable():
                    return False
            return True

    @api.multi
    def check_bookable(self):
        for rec in self:
            for line in rec.order_line:
                if not line.check_bookable():
                    return False
            return True

    @api.multi
    @api.constrains('state')
    def _check_state(self):
        if self.search_count([('state', 'not in', ['draft'])]) and \
                self.env['sale.order.line'].sudo().search_count([('order_id', '=', self.id), ('overlap', '=', 'True')]):
            raise ValidationError(_(
                'There are lines with overlap in this order. Please move overlapping lines to another time or resource'))


def seconds(td):
    assert isinstance(td, timedelta)

    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10. ** 6
