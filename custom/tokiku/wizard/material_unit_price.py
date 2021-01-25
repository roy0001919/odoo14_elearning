from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class MaterialUnitPriceLine(models.TransientModel):
    _name = 'tokiku.material_unit_price.line'
    _description = 'Material Unit Price Line'

    name = fields.Char('Name')
    raw_pricing_total_weight = fields.Float('Total Weight', digits=(16, 3))
    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float('Unit Price')
    total_price = fields.Float('Total Price', store=True)

    @api.onchange('price_unit')
    def _onchange_tmp_grid(self):
        self.total_price = round((self.price_unit * self.raw_pricing_total_weight))


class MaterialUnitPrice(models.TransientModel):
    _name = 'tokiku.material_unit_price'
    _description = 'Material Unit Price'

    tmp_grid = fields.Many2many('tokiku.material_unit_price.line', string='Grid')
    partner_id = fields.Many2one('res.partner', string='Supplier')


    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        get_supplier_id = self.env.context.get('default_supplier_id')
        self.partner_id = get_supplier_id
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')

        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        material_categ = {}
        wizard_lines = []

        if order.categ_code == 'raw':
            for line in order.order_line:
                if line.name in material_categ:
                    material_categ[line.name] += line.raw_pricing_total_weight
                else:
                    material_categ[line.name] = line.raw_pricing_total_weight

            for categ_line in material_categ:
                wizard_lines.append((0, 0, {'name': categ_line,
                                            'raw_pricing_total_weight': material_categ[categ_line],
                                            'product_id': line.product_id.id,
                                        }))

        if order.categ_code == 'aluminum':
            for line in order.order_line:
                if line.material in material_categ:
                    material_categ[line.material] += line.refine_pricing_total_weight
                else:
                    material_categ[line.material] = line.refine_pricing_total_weight

            for categ_line in material_categ:
                wizard_lines.append((0, 0, {'name': categ_line,
                                            'raw_pricing_total_weight': material_categ[categ_line],
                                            'product_id': line.product_id.id,
                                        }))

        elif order.categ_code == 'glass':
            for line in order.order_line:
                if line.material in material_categ:
                    material_categ[line.material] += line.refine_pricing_total_weight
                else:
                    material_categ[line.material] = line.refine_pricing_total_weight

            for categ_line in material_categ:
                wizard_lines.append((0, 0, {'name': categ_line,
                                            'raw_pricing_total_weight': material_categ[categ_line],
                                            'product_id': line.product_id.id,
                                        }))
        elif order.categ_code == 'plate':
            for line in order.order_line:
                if line.material in material_categ:
                    material_categ[line.material] += line.refine_pricing_total_weight
                else:
                    material_categ[line.material] = line.refine_pricing_total_weight

            for categ_line in material_categ:
                wizard_lines.append((0, 0, {'name': categ_line,
                                            'raw_pricing_total_weight': material_categ[categ_line],
                                            'product_id': line.product_id.id,
                                        }))
        elif order.categ_code == 'steel':
            for line in order.order_line:
                if line.material in material_categ:
                    material_categ[line.material] += line.refine_pricing_total_weight
                else:
                    material_categ[line.material] = line.refine_pricing_total_weight

            for categ_line in material_categ:
                wizard_lines.append((0, 0, {'name': categ_line,
                                            'raw_pricing_total_weight': material_categ[categ_line],
                                            'product_id': line.product_id.id,
                                        }))
        elif order.categ_code == 'iron':
            for line in order.order_line:
                if line.material in material_categ:
                    material_categ[line.material] += line.refine_pricing_total_weight
                else:
                    material_categ[line.material] = line.refine_pricing_total_weight

            for categ_line in material_categ:
                wizard_lines.append((0, 0, {'name': categ_line,
                                            'raw_pricing_total_weight': material_categ[categ_line],
                                            'product_id': line.product_id.id,
                                        }))
        self.tmp_grid = wizard_lines


    @api.multi
    def back_po(self):
        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)
        for rec in self:
            for s in rec.tmp_grid:
                self.env['purchase.order.line'].search([('material', 'like', s.name)]).write(
                    {'material_unit_prices': s.price_unit})
        total_price = 0
        if order.categ_code == 'raw':
            for rec in self.tmp_grid:
                for line in order.order_line:
                    if line.name == rec.name:
                        line.price_unit = round((line.raw_pricing_single_weight * rec.price_unit), 6)
                        line.material_total = round((line.product_qty * line.price_unit), 6)
                        total_price += line.material_total
                        line.valuation_price = rec.price_unit
                    for tax in order:
                        tax.amount_untaxed = total_price
        else:
            for rec in self.tmp_grid:
                for line in order.order_line:
                    if line.material == rec.name:
                        line.price_unit = rec.price_unit * line.refine_pricing_single_weight
                        line.valuation_price = rec.price_unit

        return {'type': 'ir.actions.act_window_close'}




        # if order and order.categ_code == 'mold':
        #     form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_mold_order_form')[1]
        # elif order and order.categ_code == 'raw':
        #     form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_raw_order_form')[1]
        # else:
        #     form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_order_form')[1]

        # return {
        #     'name': _('Purchase Order'),
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'purchase.order',
        #     'views': [(form_id, 'form')],
        #     'type': 'ir.actions.act_window',
        #     'target': 'current',
        #     'res_id': get_order_id,
        # }

    # get_panel_id = self.env.context.get('panel_id')
    # panel = self.env['tokiku.panel'].browse(get_panel_id)