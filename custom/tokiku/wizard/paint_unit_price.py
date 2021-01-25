from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class PaintUnitPriceLine(models.TransientModel):
    _name = 'tokiku.paint_unit_price.line'
    _description = 'Paint Unit Price Line'

    name = fields.Char('Surface Coating')
    color_code = fields.Char('Color Code')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure')
    price_unit = fields.Float('Price Unit')


class PaintUnitPrice(models.TransientModel):
    _name = 'tokiku.paint_unit_price'
    _description = 'Paint Unit Price'

    tmp_grid = fields.Many2many('tokiku.paint_unit_price.line', string='Grid')
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
                                                'product_uom_id': line.product_uom.id
                                                }))
                    paint_categ.append(group_key)

        self.tmp_grid = wizard_lines
        # print ("tmp_grid %s" % self.tmp_grid)


    @api.multi
    def back_po(self):
        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        for rec in self:
            for s in rec.tmp_grid:
                self.env['purchase.order.line'].search([('surface_coating', 'like', s.name)
                    ,('color_code', 'like', s.color_code)]).write({'paint_unit_prices': s.price_unit})

        for line in order.order_line:
            for rec in self.tmp_grid:
                if line.surface_coating == rec.name and line.color_code == rec.color_code:

                    line.product_uom = rec.product_uom_id.id
                    line.valuation_price = rec.price_unit
                    if rec.product_uom_id.name == 'm2':
                        line.price_unit = line.paint_area * rec.price_unit
                    elif rec.product_uom_id.name == 'kg':
                        line.price_unit = line.refine_pricing_single_weight * rec.price_unit
                    elif rec.product_uom_id.name == 'piece':
                        line.price_unit = line.surface_coating_qty * rec.price_unit

        return {'type': 'ir.actions.act_window_close'}



        # for rec in self.tmp_grid:
        #     for line in order.order_line:
        #         if rec.unit == 'm2':
        #             line.unit_area = line.cutting_width
        #             line.area = line.unit_area / 1000.0 * line.order_length / 1000.0
        #         if rec.unit == 'kg':
        #             line.weight = line.refine_weight * line.order_length / 1000.0
        #         if rec.unit == 'piece':
        #             line.surface_coating_qty = line.product_qty


        # form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_process_order_form')[1]


        # return {
        #     'name': _('Purchase Order'),
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'purchase.order',
        #     'views': [(form_id, 'form')],
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #     'res_id': get_order_id,
            # 'context': {'default_categ_id': categ.id,},
        # }
