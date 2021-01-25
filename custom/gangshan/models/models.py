# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DDF
from datetime import datetime
import pytz
import logging
import xmlrpclib

_logger = logging.getLogger(__name__)
po_syncing = {'syncing': False}


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    p_date = fields.Char('Date for Print', compute='_compute_p_date', store=True)
    order_user = fields.Char(related='partner_id.name')
    order_num = fields.Char(related='order_id.name')

    @api.depends('booking_start')
    def _compute_p_date(self):
        tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        for rec in self:
            if rec.booking_start:
                rec.p_date = datetime.strftime(
                    datetime.strptime(rec.booking_start, DTF).replace(tzinfo=pytz.utc).astimezone(tz), DDF)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def sync_data(self):
        if not po_syncing['syncing']:
            po_syncing.setdefault('syncing', True)
            _logger.info('pass data to server')
            # get pos sale when is_sync is false

            posids = self.env['pos.order'].search([('is_sync', '=', False)], order='id')
            postArr = []
            for posid in posids:
                x = 0
                pid = posid.partner_id
                user = self.env['res.users'].search([('id', '=', posid.user_id.id)])
                prod = self.env['product.product'].with_context({'lang': user.lang})
                if not pid:
                    pid = user.partner_id
                for line in posid.lines:
                    addsolids = []
                    prod = prod.search([('id', '=', line.product_id.id)])
                    for i in range(int(line.qty)):
                        x += 1
                        addsolids.append((0, False, {
                            'name': u'%s-%s' % (posid.pos_reference, x),
                            'product_id': prod.id,
                            'product_uom_qty': 1,
                            'price_unit': line.price_unit,
                            'booking_start': line.booking_start,
                            'booking_end': line.booking_end,
                            'booking_batch': line.booking_batch,
                            'ticket': '',
                            'checkin_time': line.checkin_time,
                            'remark3': '',
                        }))

                    postdata = {
                        'partner_id': pid.id,
                        'state': 'sale',
                        'origin': line.origin,
                        'order_line': addsolids,
                        'note': u'%s' % posid.pos_reference,
                    }

                    postArr.append(postdata)
                _logger.info('pass data to server : x=%s' % x)
            # post data to server
            if len(postArr) > 0:
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
                    obj = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
                    ret = obj.execute_kw(db, uid, pwd, 'sale.order', 'create_order_from_pos', [postArr])

                    for it in ret:
                        _logger.info('it: %s' % it)
                        posids = self.env['pos.order'].search([('pos_reference', '=', it)])
                        _logger.info('posids: %s' % posids)
                        posids.is_sync = True

            po_syncing.setdefault('syncing', False)
