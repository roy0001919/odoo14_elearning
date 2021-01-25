# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


class AccountInvoice(models.Model):
    _inherit = 'account.invoice.line'

    atlas_id = fields.Many2one('tokiku.atlas', 'Processing Atlas', related='purchase_line_id.atlas_id')
    qty_done = fields.Float(string='Arrival quantity', default=0.0)# , compute='_compute_qty_done', store=True
    qty_invoiced = fields.Float(string="Purchase Qty", compute='_compute_qty_invoiced', store=True)

    # @api.multi
    # @api.depends('purchase_line_id.order_id.picking_ids.pack_operation_ids.qty_done')
    # def _compute_qty_done(self):
    #     for rec in self:
    #         for pick in rec.purchase_line_id.order_id.picking_ids:
    #             for pack in pick.pack_operation_ids:
    #                 if rec.product_id == pack.product_id:
    #                     rec.qty_done = pack.qty_done

    @api.multi
    @api.depends('purchase_line_id.qty_invoiced')
    def _compute_qty_invoiced(self):
        for rec in self:
            rec.qty_invoiced = rec.purchase_line_id.qty_invoiced - rec.quantity

    @api.onchange('quantity')
    def onchange_qty_invoiced(self):
        for rec in self:
            if rec.quantity + rec.purchase_line_id.qty_invoiced > rec.qty_done:
                rec.quantity = 0
                return {
                    'warning': {
                        'title': 'Wrong quantity',
                        'message': 'Purchase quantity cannot be greater than the ordered quantity',
                    }
                }