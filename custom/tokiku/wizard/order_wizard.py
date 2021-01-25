# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderGrid(models.TransientModel):
    _name = 'tokiku.purchase_order_grid'

    ref_prod = fields.Char('Product')
    name = fields.Char('Work Item')
    qty = fields.Char('Qty')

    po_wizard_id = fields.Many2one('tokiku.po_wizard')


class CreatePOFromWizard(models.TransientModel):
    _name = 'tokiku.po_wizard'
    _description = 'Create PO from Wizard'

    # tmp_grid = fields.One2many('tokiku.purchase_order_grid', 'po_wizard_id', string='Grid')
    tmp_grid = fields.One2many('tokiku.purchase_order_grid', 'po_wizard_id', string='Grid')


    # @api.multi
    # def create_po(self):
		# pass
    #     if order and order.categ_code == 'mold':
    #         form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_mold_panel_order_form')[1]
    #     elif order and order.categ_code == 'raw':
    #         form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_raw_panel_order_form')[1]
    #     else:
    #         form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_order_form')[1]
    #
    #     return {
    #         'name': _('Purchase Order'),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'purchase.order',
    #         'views': [(form_id, 'form')],
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'res_id': get_order_id,
    #     }