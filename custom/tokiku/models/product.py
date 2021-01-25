# -*- coding: utf-8 -*-
import collections
import json
from lxml import etree
import odoo.addons.decimal_precision as dp
from core.biznavi.utils import parse_float
from odoo import api, fields, models, _
import logging

from odoo.osv.orm import setup_modifiers

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    market_price = fields.Float('Market Price', digits=dp.get_precision('Product Price'))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    project_id = fields.Many2one('project.project', string='Project')
    project_short_name = fields.Char('Project Short Name', related='project_id.short_name')
    category_code = fields.Char(related='categ_id.code', store=True)

    part_no = fields.Char(string='Part Number')
    seller_ids = fields.One2many('product.supplierinfo', 'product_id', 'Vendors')
    product_seller_id = fields.Many2one('product.supplierinfo', compute='_compute_seller_id', store=True)
    supplier_name = fields.Many2one('res.partner', string='Supplier Name', compute='_compute_supplier_name', store=True)
    supplier_short_name = fields.Char('supplier short name',related='supplier_name.ref')
    supplier_part_no = fields.Char(string='Supplier Part Number', compute='_compute_supplier_part_no', store=True)
    # material = fields.Char(string='Material')
    order_length = fields.Char('Order Length')
    order_width = fields.Float('Order Width')
    size = fields.Char('Size')
    pack_operation_ids = fields.One2many("stock.pack.operation", 'product_id')

    # '''Mold specialize : add product_seller_id field to provide many supplier for one product.'''
    paint_area = fields.Float('Paint Area')# related='product_seller_id.paint_area'
    coating = fields.Float('Coating', related='product_seller_id.coating')
    ingot = fields.Char('Ingot', related='product_seller_id.ingot')
    material = fields.Char(string='Material', related='product_seller_id.product_material', store=True)
    net_weight = fields.Float(string='Net Weight', related='product_seller_id.weight')
    # '''Mold specialize : add product_seller_id field to provide many supplier for one product.'''

    min_qty = fields.Float(string='Minimal Quantity', compute='_compute_min_qty')
    mold_line_ids = fields.One2many('tokiku.mold_line', 'product_id')
    mold_assembly_cost = fields.Float(string='Mold Assembly Cost', compute='_compute_mold_cost', digits=dp.get_precision('Product Price'))
    description = fields.Char('Description')
    remarks = fields.Char('Remarks')
    # length = fields.Float(string='Length')

    color_code = fields.Char('Color Code')
    heating = fields.Char('Heating')
    surface_coating = fields.Char('Surface Coating') # for altas use,
    # mold_part_ids = fields.Many2one('tokiku.mold_combination')
    mold_part_ids = fields.One2many('tokiku.mold_part', 'product_id', 'Mold Parts')
    mold_usage_status = fields.Selection([('can be used', 'Can be used'),
                                     ('stop using(design changed, mold can be used)', 'Stop Using(Design Changed, Mold can be used)'),
                                     ('stop using(design changed, mold cannot be used)', 'Stop Using(Design Changed, Mold cannot be used)'),
                                     ('stop using(scrapped)', 'Stop Using(Scrapped)')],
                                    string='Mold Usage Status', default="can be used")

    mold_drawing_info_ids = fields.One2many('tokiku.mold_drawing_info', 'product_id', 'Mold Drawing Info')
    material_section_info_ids = fields.One2many('tokiku.material_section_info', 'product_id', 'Material Section Info')

    raw_supplier_name = fields.Many2one('res.partner', string='Supplier Name')
    raw_supplier_part_no = fields.Char(string='Supplier Part Number')
    raw_material = fields.Char(string='Material')

    # mold_line = fields.Many2one('tokiku.mold_line', string='Product Mold Line')
    mold_id = fields.Many2one('product.product', string='Mold Reference', compute='_compute_mold_id', store=True) # compute='_compute_mold_id', store=True

    @api.multi
    @api.depends('project_id', 'categ_id', 'name', 'default_code', 'part_no')  # 'category_code',
    def _compute_mold_id(self):
        for rec in self:
            if rec.category_code == 'aluminum':
                mold = self.env['product.product'].search(
                    [('category_code', '=', 'mold'),
                     ('default_code', '=', rec.part_no)], limit=1)
                # print ("mold %s" % mold)
                if mold:
                    rec.mold_id = mold.id
            elif rec.category_code == 'raw':
                mold = self.env['product.product'].search(
                    [('category_code', '=', 'mold'),
                     ('default_code', '=', rec.default_code)], limit=1)
                # print ("mold %s" % mold)
                if mold:
                    rec.mold_id = mold.id

    @api.multi
    def po_count(self):
        tree_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_order_form')[1]
        return {
            'name': _('Product Purchase List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [
                ('state', 'in', ['purchase', 'done']),
                ('product_id', 'in', self.mapped('id'))
            ]
        }

    # @api.multi
    # def open_table(self):
    #     pass
        # tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'mold_product_table_view')[1]
        # form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'mold_product_table_view')[1]
        # return {
        #     'name': _('Table'),
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'product.product',
        #     'views': [(form_id, 'form')],
        #     'type': 'ir.actions.act_window',
        #     'target': 'current',
        #     'domain': [
        #         ('category_code', '=', 'mold')]
        # }



    @api.multi
    def _compute_mold_cost(self):
        for p in self:
            if len(p.mold_part_ids) != 0:
                mold_assembly_cost = 0
                for s in p.mold_part_ids:
                    if p.project_short_name == s.project_short_name:
                        mold_assembly_cost += s.price
                    else:
                        continue

                # p.mold_assembly_cost = mold_assembly_cost
                # print p.mold_assembly_cost
                p.mold_assembly_cost = round(mold_assembly_cost)
                # print p.mold_assembly_cost
            # else:
            #     mold_order = p.env['purchase.order'].search([('product_id', '=', p.id)])
            #     for order in mold_order:
            #         order.

                # print mold_order
        # for p in self:
        #     for s in p.seller_ids:
        #         p.supplier_name = s.name
        #         break

        # domain = [
        #     ('state', 'in', ['purchase', 'done']),
        #     ('product_id', 'in', self.mapped('id')),
        # ]
        # PurchaseOrderLines = self.env['purchase.order.line'].search(domain)
        # for product in self:
        #     product.purchase_count = len(
        #         PurchaseOrderLines.filtered(lambda r: r.product_id == product).mapped('order_id'))
    # @api.multi
    # def _sales_count(self):
    #     r = {}
    #     domain = [
    #         ('state', 'in', ['sale', 'done']),
    #         ('product_id', 'in', self.ids),
    #     ]
    #     for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
    #         r[group['product_id'][0]] = group['product_uom_qty']
    #     for product in self:
    #         product.sales_count = r.get(product.id, 0)
    #     return r


    @api.multi
    @api.depends('seller_ids.supplier_name', 'seller_ids')
    def _compute_supplier_name(self):
        for p in self:
            for s in p.seller_ids:
                p.supplier_name = s.name
                break

    @api.multi
    @api.depends('seller_ids', 'seller_ids.product_code')
    def _compute_supplier_part_no(self):
        for p in self:
            for s in p.seller_ids:
                p.supplier_part_no = s.product_code
                break

    @api.multi
    def _compute_min_qty(self):
        for p in self:
            for s in p.seller_ids:
                p.min_qty = s.min_qty
                break

    @api.multi
    def _compute_ingot(self):
        for p in self:
            sup_info = self.env['product.supplierinfo'].sudo().search(
                [('product_id', '=', p.product_id.id), ('name', '=', p.supplier_name.id)])
            if sup_info and len(sup_info) == 1:
                p.ingot = sup_info[0].ingot


    @api.multi
    @api.depends('product_seller_id.supplier_name')
    def _compute_seller_id(self):
        for p in self:
            sup_info = self.env['product.supplierinfo'].search(
                [('product_id', '=', p.id), ('supplier_name', '=', p.supplier_name.name)])
            if len(sup_info) > 0:
                p.product_seller_id = sup_info[0]
    # @api.multi
    # def get_variant_product(self, name, value):
    #     for p in self.sudo():
    #         attribute = self.env['product.attribute'].sudo().with_context({'lang': 'en_US'}).search([('name', '=', name)])
    #         if not attribute:
    #             attribute = self.env['product.attribute'].sudo().create({'name': name})
    #         attr_value = self.env['product.attribute.value'].sudo().with_context({'lang': 'en_US'}).search([('attribute_id', '=', attribute.id), ('name', '=', str(value))])
    #         if not attr_value:
    #             attr_value = self.env['product.attribute.value'].sudo().create({
    #                 'attribute_id': attribute.id,
    #                 'name': str(value)
    #             })
    #         # attr_value.attribute_id = attribute
    #         # product = self.env['product.product'].sudo().search([('attribute_value_ids', '=', attribute.id)])
    #         # if not product:
    #         #     product = self.env['product.product'].sudo().create({
    #         #         'product_tmpl_id': p.id,
    #         #         'attribute_value_ids': [(6, 0, [attribute.id])]
    #         #     })
    #
    #         attribute_line = self.env['product.attribute.line'].sudo().search([('product_tmpl_id', '=', p.id), ('attribute_id', '=', attribute.id)])
    #         if not attribute_line:
    #             attribute_line = self.env['product.attribute.line'].sudo().create({'product_tmpl_id': p.id, 'attribute_id': attribute.id})
    #         attribute_line.write({'value_ids': [(4, attr_value.id)]})
    #         p.sudo().create_variant_ids()
    #         product = self.env['product.product'].sudo().search([('product_tmpl_id', '=', p.id), ('attribute_value_ids', '=', attr_value.id)])
    #         product.write({'volume': parse_float(product.attribute_value_ids.name), 'weight': product.product_tmpl_id.weight})
    #
    #         return product
            # product.material = material
            # product.net_weight = net_weight
            # product.supplier_part_no = supplier_part_no
            # return p.product_variant_ids[0]
            # self.product_tmpl_id.write({'attribute_value_ids': [(6, 0, [attr_value.id])]})


class ProductCategory(models.Model):
    _inherit = 'product.category'

    code = fields.Char(string='Category Code')
    keywords = fields.One2many('tokiku.category_keyword', 'categ_id', string='Category Keyword', ondelete='cascade')
    panel_categ_id = fields.Many2one('product.category', compute='_compute_panel_categ', store=True)  # , store=True

    @api.multi
    @api.depends('parent_id')
    def _compute_panel_categ(self):
        panel_cats = self.env['product.category'].search([('code', '!=', False)])
        for c in self:
            if c.id in [cat.id for cat in panel_cats]:
                c.panel_categ_id = c.id
            elif c.parent_id:
                panel_cat = c.parent_id
                while panel_cat.id not in [cat.id for cat in panel_cats] and panel_cat.parent_id:
                    panel_cat = panel_cat.parent_id
                c.panel_categ_id = panel_cat


class ProductCategoryKeyword(models.Model):
    _name = 'tokiku.category_keyword'

    name = fields.Char('Name')
    categ_id = fields.Many2one('product.category')


class MoldPart(models.Model):
    _name = 'tokiku.mold_part'

    # name = fields.Char('Mold Part Desc')
    name = fields.Many2one('tokiku.mold_combinaiton', string='Mold Part Desc', ondelete='restrict')
    price = fields.Float('Price(w/o VAT)')
    mold_spec = fields.Char(string='Mold Spec')
    product_id = fields.Many2one('product.product')
    project_id = fields.Many2one('project.project', string='Projects')
    project_short_name = fields.Char('Project Short Name', related='project_id.short_name')

    product_part_no = fields.Char(related='product_id.default_code', store=True)
    supplier_name = fields.Many2one(related='product_id.supplier_name')
    supplier_short_name = fields.Char('supplier short name', related='supplier_name.ref')
    supplier_part_no = fields.Char(related='product_id.supplier_part_no')
    # ingot = fields.Char(related='product_id.ingot')
    ingot = fields.Char('Ingot', related='product_id.ingot')
    remark = fields.Char('Remark')
    short_name = fields.Char(related='product_id.supplier_name.ref')

    @api.onchange('project_id')
    def project_id_onchange(self):
        for rec in self:
            rec.project_id = self.env.user.project_id.id

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"
    _order = "id"
    category_code = fields.Char(related='product_id.categ_id.panel_categ_id.code',compute='_compute_item_order', store=True)# related='product_id.categ_id.panel_categ_id.code'
    product_material = fields.Char(string='Material')
    # material = fields.Char(string='Material')
    # unit_weight = fields.Float('Unit Weight')
    weight = fields.Float('Unit Weight')
    # last_atlas = self.env['tokiku.atlas'].search([('name', '=', atlas.name)], order="atlas_version desc", limit=1)
    item_order = fields.Integer('item_order', compute='_compute_item_order')
    paint_area = fields.Float('Paint Area')
    coating = fields.Float('Coating')
    ingot = fields.Char('Ingot')
    supplier_name = fields.Char(related='name.name')


    # @api.multi
    # def _compute_category_code(self):
    #     for rec in self:
    #         if rec.product_id.categ_id:
    #             rec.category_code = rec.product_id.categ_id.panel_categ_id.code


    @api.multi
    def _compute_item_order(self):
        for rec in self:
            item_count = 1
            supplier_info = self.env['product.supplierinfo'].search([
                ('product_id', '=', rec.product_id.id)], order="id")
            if rec.product_id.categ_id:
                rec.category_code = rec.product_id.categ_id.panel_categ_id.code
            for s in supplier_info:
                s.item_order = item_count
                item_count += 1




    # @api.one
    # @api.depends('category_code', 'product_id')
    # def _compute_category_code(self):
    #     self.category_code = self.product_id.category_code
    #
    #
    # @api.one
    # @api.depends('material', 'product_id')
    # def _compute_material(self):
    #     for s in self:
    #         main_prod = s.env['product.product'].search([('supplier_name', '=', s.name)])


class MoldDrawingInfo(models.Model):
    _name = 'tokiku.mold_drawing_info'

    product_id = fields.Many2one('product.product')
    mold_drawing_trial_date = fields.Date(string='Mold Drawing Trial Date')
    mold_drawing_signing_date = fields.Date(string='Mold Drawing Signing Date')
    mold_drawing_status = fields.Selection([('未選取', '未選取'),
                                            ('合格', 'Qualified'),
                                            ('不合格', 'Unqualified'),
                                            ('停用(變更設計)', 'Stop Using(Design Changed)'),
                                            ('停用(報廢)', 'Stop Using(Scrapped)')],
                                               string='Mold Drawing Status', default="未選取")


class MaterialSectionInfo(models.Model):
    _name = 'tokiku.material_section_info'

    product_id = fields.Many2one('product.product')
    actual_delivery_date = fields.Date(string='Actual Delivery Date')
    signing_date = fields.Date(string='Signing Date')

    # material_section_status = fields.Selection([('qualified', 'Qualified'),
    #                                         ('unqualified', 'Unqualified'),
    #                                         ('stop using(design changed)', 'Stop Using(Design Changed)'),
    #                                         ('stop using(scrapped)', 'Stop Using(Scrapped)')],
    #                                            string='Material Section Status', default="qualified")
    material_section_status = fields.Selection([('未選取', '未選取'),
                                            ('合格', 'Qualified'),
                                            ('不合格', 'Unqualified'),
                                            ('停用(變更設計)', 'Stop Using(Design Changed)'),
                                            ('停用(報廢)', 'Stop Using(Scrapped)')],
                                               string='Material Section Status', default="未選取")
    stop_using_note = fields.Char(string='Stop Using Note')


# class ProductProduct(models.Model):
#     _inherit = 'product.product'


    # category_code = fields.Char(related='categ_id.code', store=True)
    # length = fields.Integer(string='Length', compute='_compute_display_length', store=True)


    # xx_qty_received = fields.Char(string='Order Quantity Unfolded', compute='_compute_qty_received')

    # @api.multi
    # @api.depends('attribute_value_ids')
    # def _compute_display_length(self):
    #     for p in self:
    #         for a in p.attribute_value_ids:
    #             if a.attribute_id.name == u'長度':
    #                 p.length = int(a.name)





    # @api.multi
    # # @api.depends('contract_id.demand_ids')
    # def _compute_xx_demand_qty(self):
    #     contract_id = self.env.context.get('contract_id')
    #     panel_id = self.env.context.get('panel_id')
    #     for p in self:
    #         contract = self.env['account.analytic.contract'].browse(contract_id)
    #         for d in contract.demand_ids:
        #     demand_lines = self.env['tokiku.demand_line'].search([('demand_id.contract_id', '=', contract_id), ('product_id', '=', p.id)])
        #     for d in demand_lines:
        #         p.demand_qty += d.qty
