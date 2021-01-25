from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class AssemblyUnitPriceLine(models.TransientModel):
    _name = 'tokiku.assembly_unit_price.line'
    _description = 'Assembly Unit Price Line'

    # name = fields.Char('Surface Coating')
    product_category = fields.Many2one('product.category')
    product_id = fields.Many2one('product.product', string='Product')
    production = fields.Char(string='Production Item')
    price_unit = fields.Float('Price Unit')


class AssemblyUnitPrice(models.TransientModel):
    _name = 'tokiku.assembly_unit_price'
    _description = 'Assembly Unit Price'

    tmp_grid = fields.Many2many('tokiku.assembly_unit_price.line', string='Grid')
    partner_id = fields.Many2one('res.partner', string='Supplier')


    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        get_supplier_id = self.env.context.get('default_supplier_id')
        self.partner_id = get_supplier_id

        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        paint_categ = []
        wizard_lines = []

        if order.stage == 'paint':
            for line in order.order_line:
                group_key = "%s/%s" % (line.surface_coating, line.color_code)
                if group_key not in paint_categ:
                    wizard_lines.append((0, 0, {'name': line.surface_coating,
                                                'color_code': line.color_code,
                                                'price_unit': line.valuation_price,
                                                'unit': line.unit if line.unit else 'piece',
                                                }))
                    paint_categ.append(group_key)

        self.tmp_grid = wizard_lines
        # print ("tmp_grid %s" % self.tmp_grid)


    @api.multi
    def back_po(self):
        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        for line in order.order_line:
            for rec in self.tmp_grid:
                if line.surface_coating == rec.name and line.color_code == rec.color_code:

                    line.unit = rec.unit
                    line.valuation_price = rec.price_unit
                    if rec.unit == 'm2':
                        line.price_unit = line.paint_area * rec.price_unit
                    elif rec.unit == 'kg':
                        line.price_unit = line.refine_pricing_single_weight * rec.price_unit
                    elif rec.unit == 'piece':
                        line.price_unit = line.surface_coating_qty * rec.price_unit

        return {'type': 'ir.actions.act_window_close'}



