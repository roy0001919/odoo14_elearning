# -*- coding: utf-8 -*-
# import pytz

from odoo import models, fields, api, SUPERUSER_ID
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def write(self, values):
        _order = super(SaleOrder, self).write(values)
        if 'payment_acquirer_id' in values:
            for order in self:
                if order.payment_acquirer_id.name in [u'一卡通', u'Line Pay']:
                    for line in order.order_line:
                        line.remark2 = order.payment_acquirer_id.name
                else:
                    for line in order.order_line:
                        line.remark2 = None

        return _order


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_order_name = fields.Char(string="Order Reference", compute="_compute_sale_order_name_defalut", store=True)
    acquirer_id = fields.Many2one(related='order_id.payment_acquirer_id', store=True)

    @api.depends('order_id')
    def _compute_sale_order_name_defalut(self):
        for rec in self:
            lines = rec.order_id.order_line
            idx = 0
            for line in lines:
                idx += 1
                if line.sale_order_name:
                    pass
                else:
                    line.sale_order_name = '%s%s' % (rec.order_id.name, str(idx))

    # @staticmethod
    # def capacity_adjust(start_dt, end_dt, capacity):
    #     _logger.info('cap: %s' % capacity)
    #     if capacity == 400 and start_dt > datetime.strptime('20171001', '%Y%m%d') and end_dt < datetime.strptime('20180101', '%Y%m%d'):
    #         capacity -= 150
    #     return capacity


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    deadline = fields.Char('Deadline')
    # deadline = fields.Char('Deadline', compute="_compute_deadline", store=True)

    # @api.multi
    # def _compute_deadline(self):
    #     tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
    #     for tx in self:
    #          date_create = datetime.strptime(tx.create_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(tz)
    #          tx.deadline = (date_create + timedelta(days=3)).strftime('%Y/%m/%d')
