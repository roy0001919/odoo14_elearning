# -*- coding: utf-8 -*-
import json
from datetime import datetime

import pytz

from core.biznavi.utils import parse_float, parse_str
from odoo import api, fields, models, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Demand(models.Model):
    _name = 'tokiku.demand'

    name = fields.Char('Name', required=False)
    supplier = fields.Many2one('res.partner', string='Supplier', required=True) # 供應商
    categ_id = fields.Many2one('product.category', 'Category')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract') # 合約
    project_id = fields.Many2one('project.project', string='Project') # 專案
    file_date = fields.Datetime(string='File Date', readonly=True, index=True, default=fields.Datetime.now) # 製單日期
    # file_date = fields.Date(string='File Date',
    #                         default=lambda self: datetime.now(pytz.timezone(self.env.user.tz)).strftime(
    #                             '%Y-%m-%d, %H:%M:%S'))
    demand_line_ids = fields.One2many('tokiku.demand_line', 'demand_id', string='Demand Line')

    demand_id = fields.Many2one('tokiku.installation_panel_line', string='Demand')
    building = fields.Char('Building Number') # 棟別 for raw demand form
    building_id = fields.Many2one('tokiku.building', string='Building') # 棟別 for installation demand form
    demand_form_num = fields.Char('Demand Form Number', required=True, readonly=True, index=True, copy=False, default='New') # 需求單號
    demand_location = fields.Char('Demand Location') # 需求位置
    # atlas_id = fields.Many2one('tokiku.atlas', string='Atlas')  # 加工圖集

    # 階段
    stage = fields.Selection([('assembly', u'組裝'),
                              ('heat', u'熱處理'),
                              ('paint', u'烤漆'),
                              ('material', u'材料'),
                              ('refine', u'加工'),
                              ('installation', u'安裝')])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('demand_form_num', 'New') == 'New':
            vals['demand_form_num'] = self.env['ir.sequence'].next_by_code('tokiku.demand') or '/'

        return super(Demand, self).create(vals)

    @api.multi
    def act_validate(self):
        self.write({'state': 'done'})

    @api.multi
    def act_import(self):
        project_id = self.env.user.project_id
        attr_id = self.env['product.attribute'].with_context(lang=None).search([('name', '=', 'Extrusion Number')])
        length_id = self.env['product.attribute'].with_context(lang=None).search([('name', '=', 'Length')])
        for d in self:
            if d.demand_line_ids.filtered(lambda x: x.invalid_fields and len(x.invalid_fields) > 5):
                raise UserError(_('Please fix the invalid field before import!'))
                return
            panel_id = self.env['tokiku.panel'].search([('project_id', '=', project_id.id), ('categ_id', '=', d.categ_id.id)])
            # panel_id._compute_order_line_ids()
            for l in self.demand_line_ids:

                product_tmpl = self.env['product.template'].with_context(lang=None).search(
                    [('name', '=', parse_str(l.material)),
                     ('categ_id', '=', l.demand_id.categ_id.id)])
                if not product_tmpl:
                    product_tmpl = self.env['product.template'].create({
                        'name': parse_str(l.material),
                        'categ_id': d.categ_id.id,
                        'type': 'consu',
                        'default_code': parse_str(l.name),
                    })

                product = self.env['product.product'].sudo().search(
                    [('project_id', '=', project_id.id),
                     ('product_tmpl_id', '=', product_tmpl.id),
                     ('name', '=', parse_str(l.material)),
                     ('default_code', '=', l.name),  # this field is tokiku default code.
                     ('raw_supplier_name', '=', l.demand_id.supplier.id),
                     ('raw_supplier_part_no', '=', l.supplier_part_no),
                     ('weight', '=', l.net_weight),
                     ('volume', '=', l.order_length)], limit=1)
                # print ("product %s" % product)

                # mold = self.env['product.product'].search(
                #     [('category_code', '=', 'mold'),
                #      ('default_code', '=', l.name)], limit=1)
                # if product and mold:
                #     product.mold_id = mold.id

                l.invalid_fields = []
                l.product_id = None

                attr_value = self.env['product.attribute.value'].sudo().with_context(lang=None).search(
                    [('attribute_id', '=', attr_id.id), ('name', '=', parse_str(l.name))])
                if not attr_value:
                    attr_value = self.env['product.attribute.value'].with_context({'active_id': product_tmpl.id}).create(
                        {'attribute_id': attr_id.id, 'name': parse_str(l.name)})
                length_value = self.env['product.attribute.value'].sudo().with_context(lang=None).search(
                    [('attribute_id', '=', length_id.id), ('name', '=', parse_str(l.order_length))])
                if not length_value:
                    length_value = self.env['product.attribute.value'].with_context({'active_id': product_tmpl.id}).create(
                        {'attribute_id': length_id.id, 'name': parse_str(l.order_length)})

                if not product:
                    # elif p.categ_code == 'raw':
                    # mold = self.env['product.product'].search(
                    #     [('category_code', '=', 'mold'),
                    #      ('default_code', '=', p.name)], limit=1)
                    mold_product = self.env['product.product'].with_context(lang=None).search(
                        [('name', '=', 'Die'), ('attribute_value_ids', '=', attr_value.id)])

                    line_id = product_tmpl.attribute_line_ids.filtered(lambda x: x.attribute_id.id == attr_id.id)
                    if not line_id:
                        line_id = self.env['product.attribute.line'].create(
                            {'product_tmpl_id': product_tmpl.id, 'attribute_id': attr_id.id})
                    line_id.value_ids = [(4, attr_value.id)]

                    length_line_id = product_tmpl.attribute_line_ids.filtered(lambda x: x.attribute_id.id == length_id.id)
                    if not length_line_id:
                        length_line_id = self.env['product.attribute.line'].create(
                            {'product_tmpl_id': product_tmpl.id, 'attribute_id': length_id.id})
                    length_line_id.value_ids = [(4, length_value.id)]

                    product = self.env['product.product'].create({
                        'project_id': project_id.id,
                        'product_tmpl_id': product_tmpl.id,
                        'default_code': parse_str(l.name),
                        'volume': parse_float(l.order_length),
                        'weight': parse_float(l.net_weight),
                        'paint_area': mold_product.paint_area,
                        'coating': mold_product.coating,
                        'ingot': mold_product.ingot,
                        'seller_ids': [(0, 0, {
                            'product_id': product.id,
                            'name': d.supplier.id,
                            'product_code': parse_str(l.supplier_part_no),
                            'min_qty': parse_float(l.min_qty)
                        })],
                        'attribute_value_ids': [(4, attr_value.id), (4, length_value.id)],
                        'raw_supplier_name': l.demand_id.supplier.id,
                        'raw_supplier_part_no': parse_str(l.supplier_part_no),
                    })
                    # if mold:
                    #     product.write({'mold_id': mold.id})

                l.product_id = product
                pl = panel_id.line_ids.filtered(lambda x: x.product_id.id == product.id)
                # pl._compute_order_lines()
                pl._compute_demand_qty()
                pl._compute_order_qty()
                pl._compute_rest_demand_qty()
                pl._compute_weight()
                pl._compute_weight_sub()

                if not pl:
                    panel_id.sudo().line_ids = [(0, 0, {'product_id': product.id,
                                                        'supplier_part_no': product.raw_supplier_part_no,
                                                        'supplier_name': product.raw_supplier_name,
                                                        'weight': product.weight,
                                                        'material': l.material,
                                                        'cutting_length': product.volume,
                                                        'demand_qty': l.qty
                                                        })]

                    panel_id.sudo().line_ids._compute_order_lines()
                    panel_id.sudo().line_ids._compute_demand_qty()
                    panel_id.sudo().line_ids._compute_order_qty()
                    panel_id.sudo().line_ids._compute_rest_demand_qty()
                    panel_id.sudo().line_ids._compute_weight()
                    panel_id.sudo().line_ids._compute_weight_sub()
            # panel_id.compute_line_ids()



    @api.multi
    def material_sum(self):
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('panel_id')

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_partner_id': self.supplier.id,
               'panel_id': panel_id,
               'demand_id': self.id,
               # 'default_stage':,
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_demand_material_sum')[1]

        return {
            'name': _('Material Sum'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.material_sum',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }


class DemandLine(models.Model):
    _name = 'tokiku.demand_line'

    name = fields.Char(string='Part Number')
    supplier_name = fields.Char(string='Supplier Name')
    supplier_part_no = fields.Char(string='Supplier Part Number')
    material = fields.Char(string='Material')
    net_weight = fields.Char(string='Net Weight')
    order_length = fields.Char(string='Order Length')
    min_qty = fields.Char(string='Minimal Quantity')
    paint_area = fields.Char(string='Paint Area')
    coating = fields.Char(string='Coating')
    ingot = fields.Char(string='Ingot')
    qty = fields.Char(string='Demand Quantity')

    product_id = fields.Many2one('product.product', string='Product')
    demand_id = fields.Many2one('tokiku.demand', string='Demand', ondelete='cascade')
    invalid_fields = fields.Char('Invalid Fields', compute='_compute_invalid_fields', store=False)

    ref_demand_form_num = fields.Char(related='demand_id.demand_form_num')
    ref_supplier = fields.Many2one(related='demand_id.supplier')
    ref_name = fields.Char(related='demand_id.name')
    ref_file_date = fields.Datetime(related='demand_id.file_date')

    @api.multi
    def _compute_invalid_fields(self):
        project_id = self.env.user.project_id
        for l in self:
            mold_product = self.env['product.product'].with_context(lang=None).search(
                [('category_code', '=', 'mold'),
                 ('default_code', '=', parse_str(l.name))])
            l.product_id = None
            invalid_fields = l.validate_mold_product(mold_product, l)
            if len(invalid_fields) == 0:
                product_tmpl = self.env['product.template'].with_context(lang=None).search(
                    [('name', '=', parse_str(l.material)),
                     ('categ_id', '=', l.demand_id.categ_id.id)])

                product = self.env['product.product'].with_context(lang=None).search(
                    [('project_id', '=', project_id.id),
                     ('product_tmpl_id', '=', product_tmpl.id),
                     ('name', '=', parse_str(l.material)),
                     ('default_code', '=', parse_str(l.name)),
                     ('raw_supplier_name', '=', l.demand_id.supplier.id),
                     ('raw_supplier_part_no', '=', parse_str(l.supplier_part_no)),
                     ('weight', '=', parse_float(l.net_weight)),
                     ('volume', '=', parse_float(l.order_length))])

                invalid_fields = l.validate_product(product, l)
                if len(invalid_fields) == 0:
                    l.product_id = product

            l.invalid_fields = json.dumps(invalid_fields)


    def validate_mold_product(self, product, l):
        invalid_fields = []
        if product and product.category_code == 'mold':
            sellers = product.seller_ids

            for sl in sellers:
                data_correct = False
                has_supplier_name = False
                has_supplier_part_no = False  # or not sellers
                has_material = False  # or not sellers
                has_net_weight = False  # or not sellers

                if sl.supplier_name == parse_str(l.demand_id.supplier.name):
                    has_supplier_name = True
                if sl.product_code == parse_str(l.supplier_part_no):
                    has_supplier_part_no = True
                if sl.product_material == parse_str(l.material):
                    has_material = True
                if sl.weight == parse_float(l.net_weight):
                    has_net_weight = True
                if has_supplier_name and has_supplier_part_no and has_material and has_net_weight:
                    data_correct = True
                    break
                else:
                    continue
            if not data_correct:
                invalid_fields.append('name')
                invalid_fields.append('supplier_name')
                invalid_fields.append('supplier_part_no')
                invalid_fields.append('material')
                invalid_fields.append('net_weight')

        else:
            invalid_fields.append('name')
            invalid_fields.append('supplier_name')
            invalid_fields.append('supplier_part_no')
            invalid_fields.append('material')
            invalid_fields.append('net_weight')

        return invalid_fields

    # noinspection PyMethodMayBeStatic
    def validate_product(self, product, l):
        invalid_fields = []
        if len(product) > 1:
            invalid_fields.append('name')
        if not product:
            invalid_fields.append('*')

        return invalid_fields
