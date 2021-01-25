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

    @api.model
    def sync_data(self):
        if not po_syncing['syncing']:
            po_syncing.setdefault('syncing', True)
            _logger.info('pass data to server')
            # get pos sale when is_sync is false
            posids = self.env['pos.order'].search([('is_sync', '=', False)], order='id')
            postArr = []
            for posid in posids:
                pid = posid.partner_id
                user = self.env['res.users'].search([('id', '=', posid.user_id.id)])
                prod = self.env['product.product'].with_context({'lang': user.lang})
                if not pid:
                    pid = user.partner_id
                for line in posid.lines:
                    addsolids = []
                    prod = prod.search([('id', '=', line.product_id.id)])
                    addsolids.append((0, False, {
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
                    postdata = {
                        'partner_id': pid.id,
                        'state': 'sale',
                        'origin': line.origin,
                        'order_line': addsolids,
                        'note': u'%s' % posid.pos_reference,
                    }

                    postArr.append(postdata)

            # post data to server
            if len(postArr) > 0:
                # settings = self.env['pos.config.settings'].search([], limit=1)
                # _logger.info('settings: %s' % settings)
                # if len(settings) == 0:
                #     _logger.error("missing config for pos sync!")
                # else:
                #     setting = settings[0]
                _logger.info('prepare connection~~~')
                ir_values = self.env['ir.values']
                url = ir_values.get_default('pos.config.settings', 'pos_rest_url')
                db = ir_values.get_default('pos.config.settings', 'pos_rest_db')
                usr = ir_values.get_default('pos.config.settings', 'pos_rest_usr')
                pwd = ir_values.get_default('pos.config.settings', 'pos_rest_pwd')
                _logger.info('connection info: %s, %s' % (url, db))

                if url and db and usr and pwd:

                    common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
                    uid = common.authenticate(db, usr, pwd, {})
                    # _logger.info('uid: %s' % uid)

                    obj = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
                    ret = obj.execute_kw(db, uid, pwd, 'sale.order', 'create_order_from_pos', [postArr])

                    # update pos order (is_sync = false)
                    for it in ret:
                        _logger.info('it: %s' % it)
                        posids = self.env['pos.order'].search([('pos_reference', '=', it)])
                        _logger.info('posids: %s' % posids)
                        posids.is_sync = True

            po_syncing.setdefault('syncing', False)

    # @api.model
    # def create(self, vals):
    #     pos_order = super(PosOrder, self).create(vals)
    #     try:
    #         self.sync_data()
    #     except:
    #         _logger.error("Can't Sync data to server: %s" % sys.exc_info()[0])
    #         _logger.error('vals: %s' % vals)
    #         po_syncing.setdefault('syncing', False)
    #     return pos_order

    # @api.multi
    # def write(self, vals):
    # 	_logger.info('vals: %s' % vals)
    # 	pos_order = super(PosOrder, self).write(vals)
    # 	try:
    # 		self.sync_upd_data()
    # 	except:
    # 		_logger.info("Can't Sync data to server")
    # 	return pos_order


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
        # settings = self.env['pos.config.settings'].search_read([], [])
        # setting = settings[len(settings) - 1]
        ir_values = self.env['ir.values']
        url = ir_values.get_default('pos.config.settings', 'pos_rest_url')
        db = ir_values.get_default('pos.config.settings', 'pos_rest_db')
        usr = ir_values.get_default('pos.config.settings', 'pos_rest_usr')
        pwd = ir_values.get_default('pos.config.settings', 'pos_rest_pwd')

        if url and db and usr and pwd:
            common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
            uid = common.authenticate(db, usr, pwd, {})
            # _logger.info('uid: %s' % uid)

            obj = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
            ret = obj.execute_kw(db, uid, pwd, 'sale.order', 'cancel_order_from_pos', [{'sol_id': int(so_id)}])

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
