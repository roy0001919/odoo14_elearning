# -*- coding: UTF-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class PaintUnitPriceLine(models.TransientModel):
    _name = 'tokiku.install_unit_price.line'
    _description = 'Install Unit Price Line'

    install_categ = fields.Many2one('tokiku.installation_category', string='Install Category')  # 安裝類別
    product_id = fields.Many2one('product.product', string='Product')
    floor = fields.Char(string='Floor')
    install_loc = fields.Many2one('tokiku.install_location', string='Install Location')
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure')
    price_unit = fields.Float('Price Unit')


class PaintUnitPrice(models.TransientModel):
    _name = 'tokiku.install_unit_price'
    _description = 'Install Unit Price'

    tmp_grid = fields.Many2many('tokiku.install_unit_price.line', string='Grid')
    partner_id = fields.Many2one('res.partner', string='Supplier')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        get_supplier_id = self.env.context.get('default_supplier_id')
        self.partner_id = get_supplier_id

        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        ins_categ = []
        wizard_lines = []

        if order.stage == 'installation':
            for line in order.order_line:
                group_key = "%s" % (line.install_loc.name)
                if group_key not in ins_categ:
                    wizard_lines.append((0, 0, {'install_categ': line.install_categ.id,
                                                'install_loc': line.install_loc.id,
                                                'price_unit': line.valuation_price,
                                                'product_uom_id': line.product_uom.id
                                                }))
                    ins_categ.append(group_key)

        self.tmp_grid = wizard_lines
        # print ("tmp_grid %s" % self.tmp_grid)

    @api.multi
    def back_po(self):
        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        for line in order.order_line:
            for rec in self.tmp_grid:
                if line.install_loc == rec.install_loc:
                    line.material_unit_prices = rec.price_unit
                    line.install_categ.name = rec.install_categ.name
                    line.product_uom = rec.product_uom_id.id
                    line.valuation_price = rec.price_unit
                    if rec.product_uom_id.name == 'm2':
                        line.price_unit = line.order_qty * rec.price_unit
                    elif rec.product_uom_id.name == 'kg':
                        line.price_unit = line.order_qty * rec.price_unit
                    elif rec.product_uom_id.name == 'piece':
                        line.price_unit = line.order_qty * rec.price_unit

        return {'type': 'ir.actions.act_window_close'}
