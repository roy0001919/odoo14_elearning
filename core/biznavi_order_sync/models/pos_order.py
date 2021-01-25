# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
import logging
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, sys
import xmlrpclib

_logger = logging.getLogger(__name__)

po_syncing = {'syncing': False}


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_sync = fields.Boolean(string='Is Sync', default=False)

    @api.multi
    def write(self, vals):
        result = super(PosOrder, self).write(vals)

        bss = self.env['account.bank.statement.line'].sudo().search([('pos_statement_id', '=', self.id)])
        acquirer_name = None
        for bs in bss:
            acquirer_name = bs.journal_id.name

        if acquirer_name:
            acq = self.env['payment.acquirer'].sudo().search([('provider', '=', 'pos'), ('name', '=', acquirer_name)])
            if not acq:
                view_id = self.env['ir.model.data'].get_object_reference('biznavi_order_sync', 'pos_acquirer_button')[1]
                acq = self.env['payment.acquirer'].sudo().create({'name': acquirer_name, 'provider': 'pos', 'view_template_id': view_id})
            orders = self.env['sale.order'].sudo().search([('note', '=', self.pos_reference)])
            for order in orders:
                if not order.payment_acquirer_id:
                    order.payment_acquirer_id = acq
            if acquirer_name in [u'一卡通', u'Line Pay']:
                for line in order.order_line:
                    line.remark2 = acquirer_name
    #     for line in self.lines:
    #         if line.origin and line.product_id.pay_online and self.state != 'cancel':
    #             self.write({'state': 'cancel'})
    #
        return result

    @api.model
    def create_so(self, po):
        sol_ids = []
        origin = None
        pay_online = False;
        for line in po.lines:
            origin = line.origin
            prod = self.with_context(pricelist=po.user_id.partner_id.property_product_pricelist.id).env['product.product'].search([('id', '=', line.product_id.id)])
            pay_online = prod.pay_online
            if not origin or (origin and not pay_online):
                if line.qty > 0 and line.price_unit == prod.price:
                    sol_ids.append((0, False, {
                        'name': prod.name_get()[0][1],
                        'product_id': prod.id,
                        'product_uom_qty': line.qty,
                        'price_unit': line.price_unit,
                        'booking_start': line.booking_start,
                        'booking_end': line.booking_end,
                        'booking_batch': line.booking_batch,
                        'ticket': line.ticket,
                        'checkin_time': line.checkin_time,
                        'remark3': line.ticket,
                    }))
        if not origin or (origin and not pay_online):
            if len(sol_ids) > 0:
                self.env['sale.order'].sudo().create({
                    'partner_id': po.user_id.partner_id.id,
                    'state': 'sale',
                    'origin': origin,
                    'order_line': sol_ids,
                    'note': u'%s' % po.pos_reference,
                })
                if origin:
                    quos = self.env['sale.order'].sudo().search([('name', '=', origin)])
                    for quo in quos:
                        quo.ref_ticket = po.name


            # if ret:
            #     retids.append(var['note'])

    @api.model
    def create(self, vals):
        pos_order = super(PosOrder, self).create(vals)
        try:
            self.create_so(pos_order)
        except:
            exctype, excval = sys.exc_info()[:2]
            _logger.error("Can't create sale order: %s, %s" % (exctype, excval))

        return pos_order


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    is_update = fields.Boolean(string='Is Update', default=False)

    origin = fields.Char(string='Reservation Number')
    ticket = fields.Char(string='Ticket Number')
    booking_start = fields.Datetime(string="Date start")
    booking_end = fields.Datetime(string="Date end")
    booking_batch = fields.Integer(string="Batch")
    checkin_time = fields.Datetime(string="Checkin Time")
    # batch_info = fields.Char(compute='_compute_batch_info', string="Batch Information")
    batch_info = fields.Char(string="Batch Information")
    product_uom_qty = fields.Float(string='Quantity', related='qty', store=True)

    product_name = fields.Char(compute='_compute_product_name_defalut', store=True)
    product_cate = fields.Char(compute='_compute_product_cate_defalut', store=True)
    product_entry = fields.Char(compute='_compute_product_entry_defalut', store=True)

    @api.model
    def update_checkin(self):
        _logger.info('update check-in time')
        poslids = self.env['pos.order.line'].search([('is_update', '=', False), ('checkin_time', '!=', False)])
        for poslid in poslids:
            ticket = poslid.ticket
            sols = self.env['sale.order.line'].search([('ticket', '=', ticket)])
            for sol in sols:
                sol.checkin_time = poslid.checkin_time
                poslid.is_update = True

    @api.depends('product_id')
    def _compute_product_name_defalut(self):
        for rec in self:
            if rec.product_id:
                rec.product_name = rec.product_id.with_context({'lang': 'zh_TW'}).name

    @api.depends('product_id')
    def _compute_product_cate_defalut(self):
        for rec in self:
            if len(rec.product_id.attribute_value_ids) > 0:
                if rec.product_id.attribute_value_ids[0]:
                    rec.product_cate = rec.product_id.attribute_value_ids[0].with_context({'lang': 'zh_TW'}).name

    @api.depends('product_id')
    def _compute_product_entry_defalut(self):
        for rec in self:
            if len(rec.product_id.attribute_value_ids) >= 2:
                if rec.product_id.attribute_value_ids[1]:
                    rec.product_entry = rec.product_id.attribute_value_ids[1].with_context({'lang': 'zh_TW'}).name

    @api.model
    def sync_cancel_sale_order(self, so_id):
        _logger.info('sync_cancel_sale_order.so_id :%s' % so_id)
        # # settings = self.env['pos.config.settings'].search_read([], [])
        # # setting = settings[len(settings) - 1]
        # ir_values = self.env['ir.values']
        # url = ir_values.get_default('pos.config.settings', 'pos_rest_url')
        # db = ir_values.get_default('pos.config.settings', 'pos_rest_db')
        # usr = ir_values.get_default('pos.config.settings', 'pos_rest_usr')
        # pwd = ir_values.get_default('pos.config.settings', 'pos_rest_pwd')
        #
        # if url and db and usr and pwd:
        #     common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        #     uid = common.authenticate(db, usr, pwd, {})
        #     # _logger.info('uid: %s' % uid)
        #
        #     obj = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
        #     ret = obj.execute_kw(db, uid, pwd, 'sale.order', 'cancel_order_from_pos', [{'sol_id': int(so_id)}])
        self.env['sale.order'].cancel_order_from_pos([{'sol_id': int(so_id)}])

        # @api.multi
        # def _compute_batch_info(self):
        # 	tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        # 	for rec in self:
        # 		if rec.booking_batch:
        # 			batch = _("Batch [ %d ]") % rec.booking_batch
        # 			if datetime.strptime(rec.booking_start, DTF).date() == datetime.strptime(rec.booking_end, DTF).date():
        # 				rec.batch_info = '%s~%s %s' % (
        # 					datetime.strftime(
        # 						datetime.strptime(rec.booking_start, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
        # 						'%Y/%m/%d %H:%M'),
        # 					datetime.strftime(
        # 						datetime.strptime(rec.booking_end, DTF).replace(tzinfo=pytz.utc).astimezone(tz), '%H:%M'),
        # 					batch)
        # 			else:
        # 				rec.batch_info = '%s~%s %s' % (
        # 					datetime.strftime(
        # 						datetime.strptime(rec.booking_start, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
        # 						'%Y/%m/%d %H:%M'),
        # 					datetime.strftime(
        # 						datetime.strptime(rec.booking_end, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
        # 						'%Y/%m/%d %H:%M'), batch)


class PosPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('pos', 'POS')])
