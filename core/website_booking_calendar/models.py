# -*- coding: utf-8 -*-
import json
import urllib
import urllib2
from datetime import datetime, timedelta
import logging
import pytz

from odoo import api, models, fields, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)
MIN_TIMESLOT_HOURS = 1
MIN_RESERVATION_MINUTES = 30
POS_MIN_RESERVATION_MINUTES = 30


class PriceList(models.Model):
    _inherit = 'product.pricelist'

    ticket_promote_start = fields.Date('Ticket Promote Start')
    ticket_promote_end = fields.Date('Ticket Promote End')


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def button_refund_sale_order(self):
        sos = {}
        for rec in self:
            if sos.has_key(rec.order_id.name) == False:
                sos[rec.order_id.name] = rec.order_id

        for soname, order in sos.items():
            result = _("Not Refundable")
            if order.amount_total > 0:
                tz = pytz.timezone(self.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
                now = datetime.strftime(datetime.now(tz), '%Y-%m-%d %H:%M:%S')
                if order.payment_acquirer_id.provider == 'esun':
                    cust_url_method_name = '%s_get_form_action_cancel_url' % (
                        order.payment_acquirer_id.provider)
                    if hasattr(order.payment_acquirer_id, cust_url_method_name):
                        method = getattr(order.payment_acquirer_id,
                                         cust_url_method_name)
                        url = method()
                        _logger.info("url: %s" % url)
                        data = urllib.urlencode(order.form_cancel_generate_values())
                        _logger.info("data: %s" % data)
                        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "*/*",
                                   "User-Agent": "biznavi_ticket-app/1", }
                        req = urllib2.Request(url, data=data, headers=headers)
                        try:
                            res = urllib2.urlopen(req)
                        except urllib2.URLError as e:
                            if hasattr(e, 'reason'):
                                _logger.warn('We failed to reach a server.')
                                _logger.warn('Reason: %s' % e.reason)
                            elif hasattr(e, 'code'):
                                _logger.warn('The server couldn\'t fulfill the request.')
                                _logger.warn('Error code: %s' % e.code)
                        else:
                            res_str = res.read()
                            _logger.info(res_str)
                            try:
                                res_data = json.loads(res_str.split('=')[1])
                            except ValueError, e:
                                res_data = {'returnCode': 'API Error'}
                                _logger.error("%s Refund Error: %s" % (order.name, res_str))
                            payments = self.env['payment.transaction'].sudo().search(
                                [("sale_order_id", "=", order.id)])
                            _logger.info("Order %s Refund Result: %s" % (order.name, res_data.get('returnCode')))
                            order.action_cancel()
                            if res_data.get('returnCode') == "00":
                                for payment in payments:
                                    payment.state = 'cancel'
                                    payment.state_message = u'退款時間 %s' % now
                                for line in order.order_line:
                                    line.remark1 = u'退款完成'
                                result = _("Ticket Refunded!")
                            else:
                                for payment in payments:
                                    payment.state = 'pending'
                                    payment.state_message = u'退款待處理 [%s] 退款時間 %s' % (
                                    res_data.get('returnCode'), now)
                                for line in order.order_line:
                                    line.remark1 = u'退款待處理'
                                result = _("Ticket Refund Processing!")
                else:
                    order.action_cancel()
                    payments = self.env['payment.transaction'].sudo().search(
                        [("sale_order_id", "=", order.id)])
                    for payment in payments:
                        if payment.state == 'authorized':
                            payment.state = 'refund'
                            payment.refund_date = datetime.now()
                            payment.state_message = u'%s \n人工退款時間:%s' % (payment.state_message, now)
                            for line in order.order_line:
                                line.remark1 = u'退款'
                        elif payment.state == 'pending':
                            payment.state = 'cancel'
                            payment.state_message = u'%s \n人工退票時間:%s' % (payment.state_message, now)
                    order.note = "%s\n人工退票時間:%s" % (order.note, now)
                    result = _("Ticket Refund Processing!")
                    order.send_refund_mail()
            else:
                order.action_cancel()
                result = _("Ticket Refunded!")

            _logger.info('%s %s' % (order.name, result))

    @api.model
    def get_booking_available_products(self, event, products):
        return products

    @api.model
    def events_to_bookings(self, events):
        calendar_obj = self.env['resource.calendar']
        resource_obj = self.env['resource.resource']
        lang_obj = self.env['res.lang']
        lang = lang_obj.search([('code', '=', self.env.context.get('lang'))])
        user_df = ('%s %s' % (lang.date_format, lang.time_format)) if lang else DTF
        products = self.env['product.product'].search([('calendar_id', '!=', False),
                                                       ('website_published', '=', True)])
        bookings = {}
        partner = self.env.user.partner_id
        pricelist_id = partner.property_product_pricelist.id
        for event in events:
            r = event['resource']
            if r not in bookings:
                bookings[r] = {}
            start_dt = datetime.strptime(event['start'], DTF)
            end_dt = datetime.strptime(event['end'], DTF)
            # check products and its working calendars by every hour booked by user
            hour_dt = start_dt
            while hour_dt < end_dt:
                hour = hour_dt.strftime(DTF)
                if hour_dt < end_dt:
                    bookings[r][hour] = {
                        'start': hour_dt,
                        'start_f': (hour_dt).strftime(user_df),
                        'end': (hour_dt + timedelta(hours=MIN_TIMESLOT_HOURS)),
                        'end_f': (hour_dt + timedelta(hours=MIN_TIMESLOT_HOURS)).strftime(user_df),
                        'resource': resource_obj.browse(int(event['resource'])),
                        'products': {}
                    }
                    hour_end_dt = hour_dt + timedelta(hours=MIN_TIMESLOT_HOURS)
                    duration = seconds(hour_end_dt - hour_dt) / 3600
                    for product in self.get_booking_available_products(event, products):
                        hours = product.calendar_id.get_working_accurate_hours(hour_dt, hour_end_dt)
                        if hours == duration:
                            bookings[r][hour]['products'][str(product.id)] = {
                                'id': product.id,
                                'name': product.name,
                                'quantity': 1,
                                'currency': product.company_id.currency_id.name
                            }
                    # join adjacent hour intervals to one SO position
                    for h in bookings[r]:
                        if h == hour or bookings[r][h]['products'].keys() != bookings[r][hour]['products'].keys():
                            continue
                        adjacent = False
                        if bookings[r][hour]['start'] == bookings[r][h]['end']:
                            adjacent = True
                            bookings[r][h].update({
                                'end': bookings[r][hour]['end'],
                                'end_f': bookings[r][hour]['end_f']
                            })
                        elif bookings[r][hour]['end'] == bookings[r][h]['start']:
                            adjacent = True
                            bookings[r][h].update({
                                'start': bookings[r][hour]['end'],
                                'start_f': bookings[r][hour]['start_f']
                            })
                        if adjacent:
                            for id, p in bookings[r][h]['products'].iteritems():
                                bookings[r][h]['products'][id]['quantity'] += bookings[r][hour]['products'][id]['quantity']
                            del bookings[r][hour]
                            break
                hour_dt += timedelta(hours=MIN_TIMESLOT_HOURS)
        # calculate prices according to pricelists
        for k1, v1 in bookings.iteritems():
            for k2, v2 in v1.iteritems():
                for id, product in v2['products'].iteritems():
                    bookings[k1][k2]['products'][id]['price'] = self.env['product.product'].browse(product['id']).with_context({
                        'quantity': product['quantity'],
                        'pricelist': pricelist_id,
                        'partner': partner.id
                    }).price * product['quantity']
        res = []
        for r in bookings.values():
            res += r.values()
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pay_online = fields.Boolean(compute='_compute_pay_online', string='Pay Online')

    @api.multi
    def send_refund_mail(self):
        template = self.env.ref('website_booking_calendar.sale_order_refund_email_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.multi
    def _compute_pay_online(self):
        for order in self:
            order.pay_online = False
            for line in order.order_line:
                if line.product_id.pay_online:
                    order.pay_online = True

    @api.multi
    def form_cancel_generate_values(self):
        cust_method_name = '%s_form_cancel_generate_values' % (self.payment_acquirer_id.provider)
        if hasattr(self.payment_acquirer_id, cust_method_name):
            method = getattr(self.payment_acquirer_id, cust_method_name)
            return method({"reference": self.name})

    @api.multi
    def _add_booking_line(self, product_id, resource, start, end, tz_offset=0, add_qty=0, set_qty=0, batch=None, contact_usr=None, contact_tel=None, context=None, **kwargs):
        # set_qty = 1
        for rec in self:
            if start and end:
                # if not rec.env.context.get('tz'):
                #     start = datetime.strptime(start, DTF) + timedelta(minutes=tz_offset)
                #     end = datetime.strptime(end, DTF) + timedelta(minutes=tz_offset)
                # else:
                # user_tz = pytz.timezone(rec.env.context.get('tz') or 'UTC')
                user_tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
                start = user_tz.localize(fields.Datetime.from_string(start)).astimezone(pytz.utc)
                end = user_tz.localize(fields.Datetime.from_string(end)).astimezone(pytz.utc)
                # set_qty = (end - start).seconds / 3600
            if set_qty:
                quantity = set_qty
            elif add_qty is not None:
                quantity = add_qty or 0

            values = self.sudo()._website_product_id_change(rec.id, product_id, qty=quantity)
            values.update({
                'product_uom_qty': quantity,
                'resource_id': int(resource),
                'booking_start': start,
                'booking_end': end,
                'booking_batch': batch,
                'contact_usr': contact_usr,
                'contact_tel': contact_tel,
            })
            line = rec.env['sale.order.line'].sudo().with_context(tz_offset=tz_offset).create(values)
        return line

    @api.model
    def _remove_unpaid_bookings(self):
        orders = self.search([('state', '=', 'draft')])
        for order in orders:
            # if order.section_id and order.section_id.code == 'WS':
            if fields.Datetime.from_string(order.write_date) + timedelta(minutes=MIN_RESERVATION_MINUTES) < datetime.now():
                for line in order.order_line:
                    line.remark1 = u"逾時未付"

                order.action_cancel()
                _logger.info("Auto Removed Booking: %s" % order.name)

        paid_order_lines = self.env['sale.order.line'].search([('state', '=', 'sale'), ('remark1', 'in', [u"逾時未付", u'退款', ''])])
        for pol in paid_order_lines:
            pol.remark1 = None

    @api.model
    def _remove_uncheck_bookings(self):
        orders = self.search([('state', '=', 'sent')])
        for order in orders:
            needCancel = False
            for line in order.order_line:
                if fields.Datetime.from_string(line.booking_start) - timedelta(minutes=POS_MIN_RESERVATION_MINUTES) < datetime.now():
                    line.remark1 = u"逾時未取"
                    needCancel = True

            if needCancel:
                order.action_cancel()
                _logger.info("Auto Removed Uncheck Booking: %s" % order.name)


def seconds(td):
    assert isinstance(td, timedelta)

    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.**6
