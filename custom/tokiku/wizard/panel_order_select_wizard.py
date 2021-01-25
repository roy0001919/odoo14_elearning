# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import pytz

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SelectPOFromWizard(models.TransientModel):
    _name = 'tokiku.po_select_wizard'
    _description = 'Select PO Wizard'

    tmp_grid = fields.Many2many('purchase.order.line', string='Grid')
    partner_id = fields.Many2one('res.partner', string='Supplier')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        supplier_id = self.env.context.get('default_supplier_id')
        self.partner_id = supplier_id
        order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(order_id)

        exist_order_product = [l.product_id.id for l in order.order_line]

        po_dict = self.env.context.get('po_dict')

        tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'purchase')])
        for p in po_dict:
            p.update({'order_id': order_id, 'date_planned': fields.datetime.now() + timedelta(hours=8), 'taxes_id':tax_id})
        po_dict_n = list(filter(lambda x: x['product_id'] not in exist_order_product, po_dict))
        self.tmp_grid = po_dict_n

    @api.multi
    def back_po(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
        # if supplier_id:
        #     categ_ids = [s.prod_catg.id for s in panel.project_id.supplier_info_ids.filtered(lambda x: x.supplier_id == supplier_id)]

            # sup_info_id = self.env['tokiku.supplier_info'].search([('supplier_id', '=', supplier_id)])
            #
            # for sup in sup_info_id:
            #     catglist.append(sup.prod_catg)



            # if panel category in supplier product category
            # if panel and panel.categ_code == 'mold' and panel.categ_id in catglist:
            #     for line in panel.line_ids:
            #         if line.seller_id.name.id == self.partner_id.id:
            #
            #             # please note that order_length and order_width come from different place
            #             # when order product category is mold or not mold
            #
            #             if line.rest_demand_qty > 0:
            #                 if line.product_id.id not in exist_order_product:
            #                     wizard_lines.append((0, 0, {
            #                         'name': line.product_id.name,
            #                         'product_id': line.product_id.id,
            #                         'product_uom': line.product_id.uom_po_id.id,
            #                         # 'default_code': line.default_code,
            #                         'description': line.product_id.description,
            #                         'seller_id': line.seller_id.id,
            #                         'demand_qty': line.demand_qty,
            #                         'order_qty': line.rest_demand_qty,
            #                         'total_ordered_qty': line.order_qty + line.qty_backorder,
            #                         'date_planned': fields.datetime.now(),
            #                         'order_id': get_order_id,
            #                         'default_code': line.product_id.default_code,
            #                         'material': line.product_id.name,
            #                     }))
            #
            #     self.tmp_grid = wizard_lines
            #
            # if panel and panel.categ_code == 'raw':
            #     for line in panel.line_ids:
            #         if line.supplier_name.id == self.partner_id.id:
            #             # please note that order_length and order_width come from different place
            #             # when order product category is mold or not mold
            #             if line.rest_demand_qty > 0:
            #                 if line.product_id.id not in exist_order_product:
            #
            #                     wizard_lines.append((0, 0, {
            #                         'name': line.product_id.name,
            #                         'product_id': line.product_id.id,
            #                         'product_uom': line.product_id.uom_po_id.id,
            #                         # 'default_code': line.default_code,
            #                         'description': line.product_id.description,
            #                         'demand_qty': line.demand_qty,
            #                         'spare_qty': 0,
            #                         'order_qty': line.rest_demand_qty,
            #                         'total_ordered_qty': line.order_qty + line.qty_backorder,
            #                         'order_length': line.product_id.volume,
            #                         'order_width': line.product_id.order_width,
            #                         'date_planned': fields.datetime.now(),
            #                         'order_id': get_order_id,
            #                         'material': line.product_id.name,
            #                         'default_code': line.product_id.default_code,
            #                     }))
            #
            #     self.tmp_grid = wizard_lines
            #
            # if panel and panel.categ_code == 'aluminum':
            #     if order.stage == 'material':
            #         for line in panel.line_ids:
            #             if line.rest_demand_qty > 0:
            #                 if line.product_id.id not in exist_order_product:
            #                     wizard_lines.append((0, 0, {
            #                         'name': line.product_id.name,
            #                         'atlas_id': line.atlas_id.id,
            #                         'product_id': line.product_id.id,
            #                         'product_uom': line.product_id.uom_po_id.id,
            #                         'demand_qty': line.demand_qty,
            #                         'rest_demand_qty': line.rest_demand_qty,
            #                         'spare_qty': 0,
            #                         'order_qty': line.rest_demand_qty,
            #                         'total_ordered_qty': line.order_qty + line.qty_backorder,
            #                         'date_planned': fields.datetime.now(),
            #                         'order_id': get_order_id,
            #                         'order_length': line.cutting_length,
            #                         'order_width': line.cutting_width,
            #                         'code': line.code,
            #                         'color_code': line.color_code,
            #                         'surface_coating': line.surface_coating,
            #                         'description': line.description,
            #                         'pricing_area': '',
            #                         'estimated_delivery_date': '',
            #                         'default_code': line.product_id.default_code,
            #                         'material': line.material,
            #                     }))
            #         self.tmp_grid = wizard_lines
            #
            #     if len(order.stage) and order.stage != 'material':
            #         process_fee = self.env['product.product'].search([('default_code', '=', '%s_fee' % order.stage),
            #                                                           ('type', '=', 'service')], limit=1)
            #         for line in panel.line_ids:
            #             # if line.rest_demand_qty > 0:
            #             if line.product_id.id not in exist_order_product and process_fee:
            #                 wizard_lines.append((0, 0, {
            #                     'name': line.default_code,
            #                     'atlas_id': line.atlas_id.id,
            #                     'product_id': process_fee.id,
            #                     'product_uom': line.product_id.uom_po_id.id,
            #                     'demand_qty': line.demand_qty,
            #                     'product_qty': line.rest_demand_qty,
            #                     'date_planned': fields.datetime.now(),
            #                     'order_id': get_order_id,
            #                     'order_length': line.cutting_length,
            #                     'order_width': line.cutting_width,
            #                     'code': line.code,
            #                     'color_code': line.color_code,
            #                     'surface_coating': line.surface_coating,
            #                     'description': line.description,
            #                     'pricing_area': '',
            #                     'estimated_delivery_date': '',
            #                     'default_code': line.default_code,
            #                     'material': line.material,
            #                 }))
            #         self.tmp_grid = wizard_lines
            #
            # #  others
            # if panel and not panel.categ_code == 'mold' and \
            #         not panel.categ_code == 'raw' and \
            #         not panel.categ_code == 'aluminum' and \
            #         order.stage == 'material':
            #     for line in panel.line_ids:
            #
            #         if line.rest_demand_qty > 0:
            #             if line.product_id.id not in exist_order_product:
            #                 wizard_lines.append((0, 0, {
            #                     'name': line.product_id.name,
            #                     'atlas_id': line.atlas_id.id,
            #                     'product_id': line.product_id.id,
            #                     'product_uom': line.product_id.uom_po_id.id,
            #                     'demand_qty': line.demand_qty,
            #                     'spare_qty': 0,
            #                     'order_qty': line.rest_demand_qty,
            #                     'total_ordered_qty': line.order_qty + line.qty_backorder,
            #                     'date_planned': fields.datetime.now(),
            #                     'order_id': get_order_id,
            #                     'order_length': line.cutting_length,
            #                     'order_width': line.cutting_width,
            #                     'code': line.code,
            #                     'color_code': line.color_code,
            #                     'surface_coating': line.surface_coating,
            #                     'description': line.description,
            #                     'pricing_area': '',
            #                     'estimated_delivery_date': '',
            #                     'default_code': line.product_id.default_code,
            #                     'rest_demand_qty': line.rest_demand_qty,
            #                     'material': line.product_id.name,
            #                     'prod_categ_id': line.prod_categ_id.id,
            #                 }))
            #     self.tmp_grid = wizard_lines



