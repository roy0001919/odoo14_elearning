# -*- coding: utf-8 -*-
import json
from datetime import datetime

import pytz

from core.biznavi.utils import parse_float, parse_str
from odoo import api, fields, models, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Please be noticed: Only mold product use seller_ids.


class Mold(models.Model):
    _name = 'tokiku.mold'

    name = fields.Char('Name')
    categ_id = fields.Many2one('product.category', 'Category')
    project_id = fields.Many2one('project.project', string='Project')
    file_date = fields.Date(string='File Date',
                            default=lambda self: datetime.now(pytz.timezone(self.env.user.partner_id.tz)).strftime(
                                '%Y-%m-%d'))
    mold_line_ids = fields.One2many('tokiku.mold_line', 'mold_id', string='Mold Line')

    @api.multi
    def _compute_panel(self):
        for m in self:
            m.panel_id = self.env['tokiku.panel'].search(
                [('project_id', '=', m.project_id.id)], limit=1)

    @api.multi
    def act_import(self):
        for d in self:
            if d.mold_line_ids.filtered(lambda x: x.invalid_fields and len(x.invalid_fields) > 5):
                raise UserError(_('Please fix the invalid field before import!'))
                return
            panel_id = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', d.categ_id.id)], limit=1) # d.project_id.id
            product_tmpl = self.env['product.template'].with_context(lang=None).search([('name', '=', 'Die')])
            attr_id = self.env['product.attribute'].with_context(lang=None).search([('name', '=', 'Extrusion Number')])

            # panel_id._compute_order_line_ids()

            for p in panel_id.line_ids:
                p.mold_demand_qty = 0

            for l in self.mold_line_ids:
                l.invalid_fields = []
                l.product_id = None
                supplier = self.env['res.partner'].sudo().search(
                    [('supplier', '=', True), ('ref', '=', parse_str(l.supplier_name))])
                if not supplier:
                    l.invalid_fields = json.dumps(['supplier_name'])
                else:
                    attr_value = self.env['product.attribute.value'].sudo().with_context(lang=None).search(
                        [('attribute_id', '=', attr_id.id), ('name', '=', parse_str(l.code))])
                    if not attr_value:
                        attr_value = self.env['product.attribute.value'].with_context(
                            {'active_id': product_tmpl.id}).create(
                            {'attribute_id': attr_id.id, 'name': parse_str(l.code)})
                    product = product_tmpl.product_variant_ids.filtered(
                        lambda x: attr_value.id in [a.id for a in x.attribute_value_ids])

                    if not product:
                        line_id = product_tmpl.attribute_line_ids.filtered(lambda x: x.attribute_id.id == attr_id.id)
                        if not line_id:
                            line_id = self.env['product.attribute.line'].create(
                                {'product_tmpl_id': product_tmpl.id, 'attribute_id': attr_id.id})
                        line_id.value_ids = [(4, attr_value.id)]
                        product = self.env['product.product'].create({
                            'product_tmpl_id': product_tmpl.id,
                            'default_code': parse_str(l.code),
                            'attribute_value_ids': [(4, attr_value.id), ],
                        })

                        product = product_tmpl.product_variant_ids.filtered(
                            lambda x: attr_value.id in [a.id for a in x.attribute_value_ids])
                        product.project_id = self.env.user.project_id.id
                    product.description = parse_str(l.name)
                    product.paint_area = parse_str(l.paint_area)

                    seller_id = product.seller_ids.filtered(lambda x:
                                                            x.product_id.id == product.id and
                                                            x.name.id == supplier.id and
                                                            x.product_material == parse_str(l.material) and
                                                            x.product_code == parse_str(l.supplier_part_no) and
                                                            x.weight == parse_float(l.net_weight)
                                                            )
                    if seller_id:
                        seller_id.product_code = parse_str(l.supplier_part_no)
                        seller_id.min_qty = parse_float(l.min_qty)
                        seller_id.ingot = parse_str(l.ingot)
                        seller_id.coating = parse_str(l.coating)
                        # seller_id.paint_area = parse_str(l.paint_area)

                    else:
                        product.seller_ids = [(0, 0, {
                            'product_id': product.id,
                            'name': supplier.id,
                            'product_code': parse_str(l.supplier_part_no),
                            'min_qty': parse_float(l.min_qty),
                            'product_material': parse_str(l.material),
                            'weight': parse_float(l.net_weight),
                            # 'paint_area': parse_str(l.paint_area),
                            'coating': parse_str(l.coating),
                            'ingot': parse_str(l.ingot)
                        })]
                        seller_id = product.seller_ids.filtered(lambda x:
                                                                x.product_id.id == product.id and
                                                                x.name.id == supplier.id and
                                                                x.product_material == parse_str(l.material) and
                                                                x.product_code == parse_str(l.supplier_part_no) and
                                                                x.weight == parse_float(l.net_weight))

                l.product_id = product
                l.seller_id = seller_id
                pl = panel_id.line_ids.filtered(lambda x: x.product_id.id == product.id and
                                                          x.seller_id.id == seller_id.id)

                if pl:
                    panel_id.sudo().line_ids = [
                        (1, pl[0].id, {'mold_demand_qty': l.qty,
                                       'mold_expected_arrival_date': l.mold_expected_arrival_date,
                                       'material_expected_delivery_date': l.material_expected_delivery_date,
                                       })]

                    # pl._compute_order_lines()
                    pl._compute_demand_qty()
                    pl._compute_order_qty()
                    pl._compute_rest_demand_qty()
                    pl._compute_weight()
                    pl._compute_weight_sub()
                else:
                    panel_id.sudo().line_ids = [(0, 0, {'product_id': product.id,
                                                        'seller_id': seller_id.id,
                                                        'supplier_part_no': seller_id.product_code,
                                                        'weight': seller_id.weight,
                                                        'mold_demand_qty': l.qty,
                                                        'description': parse_str(l.name),
                                                        'material': product.name,
                                                        'mold_expected_arrival_date': l.mold_expected_arrival_date,
                                                        'material_expected_delivery_date': l.material_expected_delivery_date,
                                                        })]

                    # panel_id.sudo().line_ids._compute_order_lines()
                    panel_id.sudo().line_ids._compute_demand_qty()
                    panel_id.sudo().line_ids._compute_order_qty()
                    panel_id.sudo().line_ids._compute_rest_demand_qty()
                    panel_id.sudo().line_ids._compute_weight()
                    panel_id.sudo().line_ids._compute_weight_sub()
                # panel_id.refresh = True

            # panel_id.compute_line_ids()


class MoldLine(models.Model):
    _name = 'tokiku.mold_line'

    project_id = fields.Many2one('project.project', related='mold_id.project_id', string='Project')
    name = fields.Char(string='Description', default=' ')
    code = fields.Char(string='Part Number')
    supplier_name = fields.Char(string='Supplier Name')
    supplier_part_no = fields.Char(string='Supplier Part Number')
    material = fields.Char(string='Material')
    net_weight = fields.Char(string='Net Weight')
    min_qty = fields.Char(string='Minimal Quantity')
    paint_area = fields.Char(string='Paint Area')
    coating = fields.Char(string='Coating')
    ingot = fields.Char(string='Ingot')
    qty = fields.Char(string='Demand Quantity', default=1)

    product_id = fields.Many2one('product.product', string='Product')
    mold_id = fields.Many2one('tokiku.mold', string='Mold', ondelete='cascade')
    invalid_fields = fields.Char('Invalid Fields', compute='_compute_invalid_fields', store=False)
    mold_expected_arrival_date = fields.Char('Mold Exp Arrival Date')
    material_expected_delivery_date = fields.Char('Material Exp Delivery Date')


    @api.multi
    def _compute_invalid_fields(self):
        for l in self:
            # code_attr = self.env['product.attribute.value'].sudo().with_context(lang=None).search(
            #     [('name', '=', parse_str(l.code))])
            product = self.env['product.product'].with_context(lang=None).search(
                [('category_code', '=', 'mold'), ('default_code', '=', parse_str(l.code))])
            # if len(product.attribute_value_ids) == 0:
            #     product = None
            l.product_id = None
            invalid_fields = l.validate_product(product, l)
            if len(invalid_fields) == 0:
                l.product_id = product

            l.invalid_fields = json.dumps(invalid_fields)

    def validate_product(self, product, l):
        invalid_fields = []
        supplier = self.env['res.partner'].sudo().search(
            [('supplier', '=', True), ('ref', '=', parse_str(l.supplier_name))])
        if not supplier:
            invalid_fields.append('supplier_name')
            return invalid_fields
        if product:
            # sellers = product.seller_ids.filtered(lambda x: x.name.ref == parse_str(l.supplier_name))
            sellers = product.seller_ids
            # print(sellers)
            same_name_seller = []
            # for s in product.seller_ids:
            #     sellers.append(s.supplier_name)

            # has_paint_area = False or not sellers
            # has_coating = False or not sellers
            # has_ingot = False or not sellers
            # if parse_str(l.supplier_name) in sellers:
            for sl in sellers:
                data_correct = False
                has_supplier_name = False
                has_supplier_part_no = False  # or not sellers
                has_material = False  # or not sellers
                has_net_weight = False  # or not sellers
                # print(sl.supplier_name)
                # print(parse_str(l.supplier_name))
                if sl.name.ref == parse_str(l.supplier_name):
                    has_supplier_name = True
                    # print("has_supplier_name %s" % has_supplier_name)

                if sl.product_code == parse_str(l.supplier_part_no):
                    has_supplier_part_no = True
                    # print("has_supplier_part_no %s" % has_supplier_part_no)

                if sl.product_material == parse_str(l.material):
                    has_material = True
                    # print("has_material %s" % has_material)

                if sl.weight == parse_float(l.net_weight):
                    has_net_weight = True
                    # print("has_net_weight %s" % has_net_weight)

                if has_supplier_name and has_supplier_part_no and has_material and has_net_weight:
                    data_correct = True
                    break
                else:
                    continue

            if not data_correct:
                invalid_fields.append('supplier_name')
                invalid_fields.append('supplier_part_no')
                invalid_fields.append('material')
                invalid_fields.append('net_weight')

        else:
            invalid_fields.append('*')
            # append('*') means no product exists.

        return invalid_fields

        # for seller in sellers:
        #     if seller.product_code == parse_str(l.supplier_part_no):
        #         has_supplier_part_no = True
        #     if seller.material == parse_str(l.material):
        #         has_material = True
        #     if seller.weight == parse_float(l.net_weight):
        #             has_net_weight = True
        # if seller.paint_area == parse_str(l.paint_area):
        #     has_paint_area = True
        # if seller.coating == parse_str(l.coating):
        #     has_coating = True
        # if seller.ingot == parse_str(l.ingot):
        #     has_ingot = True
 # if not has_supplier_part_no:
            #     invalid_fields.append('supplier_part_no')
            # if not has_material:
            #     invalid_fields.append('material')
            # if not has_net_weight:
            #     invalid_fields.append('net_weight')
            # if not has_paint_area:
            #     invalid_fields.append('paint_area')
            # if not has_coating:
            #     invalid_fields.append('coating')
            # if not has_ingot:
            #     invalid_fields.append('ingot')

            # if product.weight != parse_float(l.net_weight):
            #     invalid_fields.append('net_weight')
            # if product.material != parse_str(l.material):
            #     invalid_fields.append('material')
            # if product.coating and product.coating != parse_str(l.coating):
            #     invalid_fields.append('coating')
            # if product.ingot and product.ingot != parse_str(l.ingot):
            #     invalid_fields.append('ingot')