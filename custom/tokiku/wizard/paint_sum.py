from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class PaintSumLine(models.TransientModel):
    _name = 'tokiku.paint_sum.line'
    _description = 'Paint Sum Line'

    name = fields.Char('Surface Coating')
    color_code = fields.Char('Color Code')
    qty = fields.Float('Qty', default=0)
    total_area = fields.Float('Total Area')
    total_weight = fields.Float('Total Weight')
    price_unit_m2 = fields.Float('Price Unit M2', compute='_compute_price_unit', store=True)
    price_unit_kg = fields.Float('Price Unit KG', compute='_compute_price_unit', store=True)
    price_unit_piece = fields.Float('Price Unit Piece', compute='_compute_price_unit', store=True)
    total_price = fields.Float('Total Price')
    product_id = fields.Many2one('product.product', string='Product')
    unit = fields.Char('Unit')
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure')

    # unit = fields.Selection([('m2', 'm2'),
    #                         ('piece', 'Piece'),
    #                         ('kg', 'kg')], string='Unit')


    # @api.onchange('price_unit')
    # def _onchange_tmp_grid(self):
    #     self.total_price = self.price_unit * self.raw_pricing_total_weight


    @api.multi
    def _compute_price_unit(self):
        for rec in self:
            if rec.product_uom_id.name == 'm2' and rec.total_area > 0:
                rec.price_unit_m2 = rec.total_price / rec.total_area
            elif rec.product_uom_id.name == 'kg' and rec.total_weight > 0:
                rec.price_unit_kg = rec.total_price / rec.total_weight
            elif rec.product_uom_id.name == 'piece' and rec.qty > 0:
                rec.price_unit_m2 = rec.total_price / rec.qty


class PaintSum(models.TransientModel):
    _name = 'tokiku.paint_sum'
    _description = 'Paint Sum'

    tmp_grid = fields.Many2many('tokiku.paint_sum.line', string='Grid')
    partner_id = fields.Many2one('res.partner', string='Supplier')


    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        get_supplier_id = self.env.context.get('default_supplier_id')
        self.partner_id = get_supplier_id

        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        name = {}
        color_code = {}
        qty = {}
        total_area = {}
        total_weight = {}
        price_total = {}
        price_unit = {}

        wizard_lines = []

        if order.stage == 'paint':
            for line in order.order_line:
                group_key = "%s/%s" % (line.surface_coating, line.color_code)

                if group_key in name:
                    qty[group_key] += line.product_qty
                    total_area[group_key] += line.paint_area
                    total_weight[group_key] += line.refine_pricing_single_weight
                    price_total[group_key] += line.price_total
                else:
                    name[group_key] = line.surface_coating
                    color_code[group_key] = line.color_code
                    qty[group_key] = line.product_qty
                    total_area[group_key] = line.paint_area
                    total_weight[group_key] = line.refine_pricing_single_weight
                    price_total[group_key] = line.price_total
                    price_unit[group_key] = line.unit


            for categ_line in name:
                wizard_lines.append((0, 0, {'name': name[categ_line],
                                            'color_code': color_code[categ_line],
                                            'product_uom_id': price_unit[categ_line],
                                            'qty': qty[categ_line],
                                            'total_area': total_area[categ_line],
                                            'total_weight': total_weight[categ_line],
                                            'total_price': price_total[categ_line]
                                            }))

        self.tmp_grid = wizard_lines


