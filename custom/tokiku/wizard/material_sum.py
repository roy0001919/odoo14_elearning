# -*- coding: utf-8 -*-
from core.biznavi.utils import parse_int, parse_float
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class MaterialSumLine(models.TransientModel):
    _name = 'tokiku.material_sum.line'
    _description = 'Material Sum Line'

    name = fields.Char('Material')
    unit_weight = fields.Float('Weight', digits=(16, 3))
    length = fields.Float()
    demand_qty = fields.Integer('Demand Qty')
    rest_demand_qty = fields.Integer('Rest Demand Qty')
    rest_demand_weight = fields.Float('Rest Demand Weight')
    order_qty = fields.Integer('Order Qty')
    order_weight = fields.Float('Order Weight')

    demand_weight = fields.Float('Demand Weight', digits=(16, 3))

    received_qty = fields.Integer('Received Qty', compute='_compute_received_qty')
    not_received_qty = fields.Integer('Not Received Qty', compute='_compute_not_received_qty')
    product_id = fields.Many2one('product.product', string='Product')

    @api.multi
    def _compute_current_rest_demand_qty(self):
        for rec in self:
            current_rest_demand_qty = rec.rest_demand_qty - rec.order_qty
            if current_rest_demand_qty > 0:
                rec.current_rest_demand_qty = current_rest_demand_qty
            else:
                rec.current_rest_demand_qty = 0.0

    @api.multi
    def _compute_current_rest_demand_weight(self):
        for rec in self:
            current_rest_demand_weight = rec.rest_demand_weight - rec.order_weight
            if current_rest_demand_weight > 0:
                rec.current_rest_demand_weight = current_rest_demand_weight
            else:
                rec.current_rest_demand_qty = 0.0

    @api.multi
    def _compute_received_qty(self):
        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        pickings = self.env['stock.picking'].sudo().search([("origin", "=", order.name)])

        for rec in self:
            if not len(pickings):
                rec.received_qty = 0.0
            else:
                for p in pickings:
                    for line in p.pack_operation_product_ids:
                        rec.received_qty += line.qty_done

    @api.multi
    def _compute_not_received_qty(self):
        for rec in self:
            rec.not_received_qty = rec.order_qty - rec.received_qty


class MaterialSum(models.TransientModel):
    _name = 'tokiku.material_sum'
    _description = 'Material Sum'

    tmp_grid = fields.Many2many('tokiku.material_sum.line', string='Grid')
    partner_id = fields.Many2one('res.partner', string='Supplier')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        get_supplier_id = self.env.context.get('default_supplier_id')
        self.partner_id = get_supplier_id

        get_order_id = self.env.context.get('order_id')
        order = self.env['purchase.order'].browse(get_order_id)

        get_demand_id = self.env.context.get('demand_id')
        demand = self.env['tokiku.demand'].browse(get_demand_id)

        material_categ = {}
        wizard_lines = []

        name = {}
        unit_weight = {}
        length = {}
        demand_qty = {}  # 需求支數
        demand_weight = {}  # 需求支數
        rest_demand_qty = {}
        rest_demand_weight = {}  # 需求重量
        order_qty = {}  # 訂購支數
        order_weight = {}

        if demand:
            for line in demand.demand_line_ids:
                #group_key = "%s/%s" % (line.material, line.net_weight)

                group_key = "%s" % (line.material)
                if group_key in name:
                    demand_qty[group_key] += parse_int(line.qty)

                else:
                    name[group_key] = line.material
                    demand_qty[group_key] = parse_int(line.qty)
                    unit_weight[group_key] = parse_float(line.net_weight)
                    # demand_weight[group_key] = unit_weight[group_key] * demand_qty[group_key]
                    # round ((unit_weight[group_key] * demand_qty[group_key]), 3)
                demand_weight[group_key] = parse_float(line.net_weight) * (parse_float(line.order_length) / 1000) * demand_qty[group_key]
            for categ_line in name:
                wizard_lines.append((0, 0, {'name': name[categ_line],
                                            'demand_qty': demand_qty[categ_line],
                                            'unit_weight': unit_weight[categ_line],
                                            'demand_weight': demand_weight[categ_line],
                                            # 'demand_weight': unit_weight[categ_line] * float(demand_qty[categ_line]),
                                            }))
        elif order.categ_code == 'raw':
            for line in order.order_line:
                if material_categ.has_key(line.name):
                    material_categ[line.name] += line.raw_pricing_total_weight
                else:
                    material_categ[line.name] = line.raw_pricing_total_weight
            for categ_line in material_categ:
                wizard_lines.append((0, 0, {'name': categ_line,
                                            'raw_pricing_total_weight': material_categ[categ_line],
                                            'product_id': line.product_id.id,
                                        }))
        elif order.categ_code == 'aluminum':
            for line in order.order_line:
                group_key = "%s" % line.material
                if group_key in name:
                    demand_qty[group_key] += line.demand_qty
                    order_qty[group_key] += line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] += line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]
                else:
                    name[group_key] = line.material
                    unit_weight[group_key] = line.unit_weight
                    demand_qty[group_key] = line.demand_qty
                    order_qty[group_key] = line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] = line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]

            for categ_line in name:
                wizard_lines.append((0, 0, {'name': name[categ_line],
                                            'unit_weight': unit_weight[categ_line],
                                            'demand_qty': demand_qty[categ_line],
                                            'demand_weight': demand_weight[categ_line],
                                            'rest_demand_qty': rest_demand_qty[group_key],
                                            'rest_demand_weight': rest_demand_weight[categ_line],
                                            'order_qty': order_qty[categ_line],
                                            'order_weight': order_weight[categ_line],
                                            }))
                # order_weight = fields.Float('Order Weight')
                # rest_order_qty = fields.Float('Rest Order Qty')
                # rest_order_weight = fields.Float('Rest Order Weight')
                # received_qty = fields.Float('Received Qty')
                # not_received_qty = fields.Float('Not Received Qty')
                # product_id = fields.Many2one('product.product', string='Product')
        elif order.categ_code == 'glass':
            for line in order.order_line:
                group_key = "%s" % line.material
                if group_key in name:
                    demand_qty[group_key] += line.demand_qty
                    order_qty[group_key] += line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] += line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]
                else:
                    name[group_key] = line.material
                    unit_weight[group_key] = line.unit_weight
                    demand_qty[group_key] = line.demand_qty
                    order_qty[group_key] = line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] = line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]

            for categ_line in name:
                wizard_lines.append((0, 0, {'name': name[categ_line],
                                            'unit_weight': unit_weight[categ_line],
                                            'demand_qty': demand_qty[categ_line],
                                            'demand_weight': demand_weight[categ_line],
                                            'rest_demand_qty': rest_demand_qty[group_key],
                                            'rest_demand_weight': rest_demand_weight[categ_line],
                                            'order_qty': order_qty[categ_line],
                                            'order_weight': order_weight[categ_line],
                                            }))
        elif order.categ_code == 'plate':
            for line in order.order_line:
                group_key = "%s" % line.material
                if group_key in name:
                    demand_qty[group_key] += line.demand_qty
                    order_qty[group_key] += line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] += line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]
                else:
                    name[group_key] = line.material
                    unit_weight[group_key] = line.unit_weight
                    demand_qty[group_key] = line.demand_qty
                    order_qty[group_key] = line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] = line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]

            for categ_line in name:
                wizard_lines.append((0, 0, {'name': name[categ_line],
                                            'unit_weight': unit_weight[categ_line],
                                            'demand_qty': demand_qty[categ_line],
                                            'demand_weight': demand_weight[categ_line],
                                            'rest_demand_qty': rest_demand_qty[group_key],
                                            'rest_demand_weight': rest_demand_weight[categ_line],
                                            'order_qty': order_qty[categ_line],
                                            'order_weight': order_weight[categ_line],
                                            }))
        elif order.categ_code == 'steel':
            for line in order.order_line:
                group_key = "%s" % line.material
                if group_key in name:
                    demand_qty[group_key] += line.demand_qty
                    order_qty[group_key] += line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] += line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]
                else:
                    name[group_key] = line.material
                    unit_weight[group_key] = line.unit_weight
                    demand_qty[group_key] = line.demand_qty
                    order_qty[group_key] = line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] = line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]

            for categ_line in name:
                wizard_lines.append((0, 0, {'name': name[categ_line],
                                            'unit_weight': unit_weight[categ_line],
                                            'demand_qty': demand_qty[categ_line],
                                            'demand_weight': demand_weight[categ_line],
                                            'rest_demand_qty': rest_demand_qty[group_key],
                                            'rest_demand_weight': rest_demand_weight[categ_line],
                                            'order_qty': order_qty[categ_line],
                                            'order_weight': order_weight[categ_line],
                                            }))
        elif order.categ_code == 'iron':
            for line in order.order_line:
                group_key = "%s" % line.material
                if group_key in name:
                    demand_qty[group_key] += line.demand_qty
                    order_qty[group_key] += line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] += line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]
                else:
                    name[group_key] = line.material
                    unit_weight[group_key] = line.unit_weight
                    demand_qty[group_key] = line.demand_qty
                    order_qty[group_key] = line.product_qty
                    rest_demand_qty[group_key] = demand_qty[group_key] - order_qty[group_key]
                    rest_demand_weight[group_key] = line.refine_pricing_single_weight * rest_demand_qty[group_key]
                    order_weight[group_key] = line.refine_pricing_single_weight * line.product_qty
                    demand_weight[group_key] = line.refine_pricing_single_weight * demand_qty[group_key]

            for categ_line in name:
                wizard_lines.append((0, 0, {'name': name[categ_line],
                                            'unit_weight': unit_weight[categ_line],
                                            'demand_qty': demand_qty[categ_line],
                                            'demand_weight': demand_weight[categ_line],
                                            'rest_demand_qty': rest_demand_qty[group_key],
                                            'rest_demand_weight': rest_demand_weight[categ_line],
                                            'order_qty': order_qty[categ_line],
                                            'order_weight': order_weight[categ_line],
                                            }))
        self.tmp_grid = wizard_lines










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