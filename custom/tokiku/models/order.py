# -*- coding: utf-8 -*-
from datetime import datetime

import odoo.addons.decimal_precision as dp
import pytz

from odoo import api, fields, models, _, SUPERUSER_ID
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OrderForm(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def open_purchase_order(self):
        if not self.env.user.contract_id:
            raise UserError(_('Please select a contract first!'))
            return

        tree_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_tokiku_order_form')[1]

        return {
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('project_id', '=', self.env.user.project_id.id)],
            'context': {'default_project_id': self.env.user.project_id.id,
                        'supplier_ids': [s.supplier_id.id for s in self.env.user.project_id.supplier_info_ids],
                        'contract_ids': [c.id for c in self.env.user.project_id.contract_ids],
                        }
        }

    # @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        for order in self:
            order.date_planned = datetime.now()

    @api.multi
    @api.depends('name', 'partner_ref')
    def name_get(self):
        result = []
        for po in self:
            name = po.name
            if po.partner_ref:
                name += ' (' + po.partner_ref + ')'
            result.append((po.id, name))
        return result

    # @api.model
    # def create(self, vals):
    #     print 'start create'
    #     result = super(OrderForm, self).create(vals)
    #     print 'end create'
    #     return result

    @api.multi
    def write(self, vals):
        panel_id = self.env.context.get('panel_id')
        if panel_id and vals.get('state') in ['purchase', 'done'] and not vals.get('panel_id'):
            vals['panel_id'] = panel_id

        result = super(OrderForm, self).write(vals)
        for rec in self:
            if len(rec.order_line) > 0 and rec.state in ['purchase', 'done', 'cancel']:
                # rec.panel_id.cal_order()
                for l in rec.order_line:
                    l.panel_line_id._compute_demand_qty()
                    l.panel_line_id._compute_order_qty()
                    l.panel_line_id._compute_rest_demand_qty()
                    l.panel_line_id._compute_weight()
                    l.panel_line_id._compute_weight_sub()
                    l.panel_line_id._compute_percent()
                    l.panel_line_id._compute_area()

                    if l.atlas_id and l.atlas_id not in rec.atlas_ids:
                        rec.atlas_ids = [(4, l.atlas_id.id)]
        # self.panel_id.refresh = True

        return result

    @api.multi
    def select_po_wizard(self):
        self.ensure_one()
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('panel_id') or self.panel_id.id
        panel = self.env['tokiku.panel'].browse(panel_id)
        supplier_id = self.partner_id.id

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               'po_dict': panel.as_po_dict(supplier_id, self.atlas_ids),
               }

        if panel.categ_code == 'mold':
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'mold_panel_order_select_wizard_view')[1]
        elif panel.categ_code == 'raw':
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'raw_panel_order_select_wizard_view')[1]
        else:
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'panel_order_select_wizard_view')[1]

        return {
            'name': _('Panel Order Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.po_select_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def install_po_wizard(self):
        self.ensure_one()
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('panel_id') or self.panel_id.id
        panel = self.env['tokiku.panel'].browse(panel_id)
        supplier_id = self.partner_id.id

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               'po_dict': panel.install_po_dict(supplier_id),
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'installation_order_select_wizard_view')[1]

        return {
            'name': _('Install Order Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.po_select_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def install_valuation_wizard(self):
        self.ensure_one()
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('panel_id') or self.panel_id.id
        panel = self.env['tokiku.panel'].browse(panel_id)
        supplier_id = self.partner_id.id

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               'po_dict': panel.install_po_dict(supplier_id),
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'installation_valuation_select_wizard_view')[
            1]

        return {
            'name': _('Install Order Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.po_select_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def item_select(self):
        self.ensure_one()
        project_id = self.env.context.get('default_project_id')
        panel_id = self.env.context.get('panel_id')

        ctx = {'default_project_id': project_id,
               'assembly_section': self.assembly_section,
               'panel_id': panel_id,
               'order_id': self.id
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'assembly_po_select_wizard_view')[1]

        return {
            'name': _('Assembly Order Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.assembly_po_select_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def material_sum(self):
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('default_panel_id') or self.panel_id.id
        stage = self.env.context.get('default_stage')

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               'default_stage': stage,
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_order_material_sum')[1]

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

    @api.multi
    def material_unit_price(self):
        self.ensure_one()
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'order_id': self.id}

        if self.categ_code == 'raw' or self.categ_code == 'aluminum' or self.categ_code == 'glass' \
                or self.categ_code == 'plate' or self.categ_code == 'iron' or self.categ_code == 'steel':
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_order_material_unit_price')[
                1]

        return {
            'name': _('Material Unit Price'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.material_unit_price',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def paint_sum(self):
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('default_panel_id') or self.panel_id.id

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_order_paint_sum')[1]

        return {
            'name': _('Paint Sum'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.paint_sum',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def paint_unit_price(self):
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('default_panel_id') or self.panel_id.id
        stage = self.env.context.get('default_stage')

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               'default_stage': stage,
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_order_paint_unit_price')[1]

        return {
            'name': _('Paint Unit Price'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.paint_unit_price',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.onchange('categ_id', 'project_id')
    def _onchange_categ_id(self):
        ci = []
        if self.project_id:
            ci = self.project_id.contract_ids

        return {'domain': {'contract_id': [('id', 'in', [c.id for c in ci])]}}

    @api.depends('order_line.move_ids')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking'].search([('group_id.name', '=', order.name)])
            order.picking_ids = pickings
            order.picking_count = len(pickings)

    @api.depends('categ_id')
    def _compute_categ_code(self):
        self.categ_code = self.categ_id.code

    new_order_num = fields.Char('Raw Order Internal', compute='_compute_order_num')
    categ_id = fields.Many2one('product.category', 'Category')
    categ_code = fields.Char(compute='_compute_categ_code', store=True)
    project_id = fields.Many2one('project.project', string='Project')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    panel_id = fields.Many2one('tokiku.panel')
    po_category_id = fields.Many2one('tokiku.order_category', string='Order Category')

    order_unit_id = fields.Many2one('tokiku.order_unit', string='Ordering Unit')
    order_department = fields.Selection([('company', 'In Company'),
                                         ('factory', 'In Factory'),
                                         ('construction', 'Construction Site'),
                                         ('not choose', 'Did Not Choose')],
                                        string='Order Department', default='not choose')  # 下訂單位
    demand_department = fields.Selection([('company', 'In Company'),
                                          ('factory', 'in Factory'),
                                          ('construction', 'Construction Site'),
                                          ('not choose', 'Did Not Choose')],
                                         string='Demand Department', default='not choose')  # 需求單位
    demand_qty_loc = fields.Char(string='demand qty location')
    partner_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory')  # 組裝廠
    # factory_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory') # 組裝廠
    payment_unit_id = fields.Many2one('tokiku.payment_unit', string='Payment Unit')
    pricing_unit_id = fields.Many2one('tokiku.pricing_unit', string='Pricing Unit')
    demand_unit_id = fields.Many2one('tokiku.demand_unit', string='Demand Unit')

    contact_id = fields.Many2one('res.partner', string='Contact')  # 聯絡人
    contact_street = fields.Many2one('res.partner', string='Street')
    shipping_address = fields.Many2one('res.partner', string='Street')  # 運送地址
    assembly_section = fields.Char(string='Assembly Section')  # 組裝工段
    assembly_categ = fields.Many2one("product.product", string='Assembly Category')  # 組裝類別
    # assembly_categ = fields.Char(string='Assembly Category')  # 組裝類別

    assembly_po_line_ids = fields.One2many('purchase.order.line', 'assembly_po_id',
                                           string='Assembly Purchase Order Line')
    is_reserved_payment = fields.Boolean(string='Is reserved payment', default=False,
                                         help="Check if the purchase order has reserved payment, otherwise it is not reserved")

    partner_id = fields.Many2one('res.partner', string='Vendor', change_default=False)  # 供應商
    partner_for_short = fields.Char(related='partner_id.ref', string='Vendor')
    stage = fields.Selection([('assembly', u'組裝'),
                              ('heat', u'熱處理'),
                              ('paint', u'烤漆'),
                              ('material', u'材料'),
                              ('refine', u'加工'),
                              ('installation', u'安裝')])  # 階段

    # atlas_id = fields.Many2one('tokiku.atlas', string='Processing Atlas', related="order_line.atlas_id")
    # atlas_name = fields.Char(string='Atlas', compute="compute_atlas_name")

    atlas_ids = fields.Many2many('tokiku.atlas', string='Processing Atlas')
    total_estimated = fields.Float(string='Estimated Total', compute='_compute_total_estimated', store=True)

    @api.multi
    @api.depends('order_line.estimated_amount')
    def _compute_total_estimated(self):
        for rec in self:
            for price in self.order_line:
                rec.total_estimated += price.estimated_amount

    # 新增顯示加工圖集 from stock.picking atlas_id
    # @api.multi
    # def compute_atlas_name(self):
    #     for rec in self:
    #         pickings = self.env['stock.picking'].search([('origin', '=', rec.name)])
    #         for ml in pickings:
    #             atlas_stock_ids = list(set([s.atlas_id for s in ml.pack_operation_product_ids]))
    #             for al in atlas_stock_ids:
    #                 if  str(al.name) != "False":
    #                     rec.atlas_name = str(rec.atlas_name) + "," + str(al.name)
    #                 else:
    #                     continue
    #             rec.atlas_name = str(rec.atlas_name).lstrip("False,")
    @api.multi
    def _compute_order_num(self):
        for o in self:
            o.new_order_num = '%s-%s-%s' % (o.project_id.project_code, o.categ_id.id, o.name[2:])

    # from purchase.order.line atlas_id
    # @api.multi
    # def compute_atlas_name(self):
    #     for rec in self:
    #         altas_lines = list(set(ol.atlas_id for ol in rec.order_line))
    #         install_lines = list(set(ol.atlas_name for ol in rec.order_line))
    #         for al in altas_lines:
    #             if str(al.name) != "False":
    #                 rec.atlas_name = str(rec.atlas_name) + "," + str(al.name)
    #             else:
    #                 continue
    #             rec.atlas_name = str(rec.atlas_name).lstrip("False,")
    #
    #         for ins in install_lines:
    #             if str(ins) != "False":
    #                 rec.atlas_name = str(rec.atlas_name) + "," + str(ins)
    #             else:
    #                 continue
    #             rec.atlas_name = str(rec.atlas_name).lstrip("False,")

    @api.multi
    def assembly_unit_price(self):
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('default_panel_id') or self.panel_id.id
        stage = self.env.context.get('default_stage')

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               'default_stage': stage,
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_assembly_unit_price')[1]

        return {
            'name': _('Assembly Unit Price'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.assembly_unit_price',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def install_unit_price(self):
        get_project_id = self.env.context.get('default_project_id')
        get_contract_id = self.env.context.get('default_contract_id')
        panel_id = self.env.context.get('default_panel_id') or self.panel_id.id
        stage = self.env.context.get('default_stage')

        ctx = {'default_project_id': get_project_id,
               'default_contract_id': get_contract_id,
               'default_supplier_id': self.partner_id.id,
               'panel_id': panel_id,
               'order_id': self.id,
               'default_stage': stage,
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_install_unit_price')[1]

        return {
            'name': _('Install Unit Price'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.install_unit_price',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    def action_estimated_amount(self):
        for rec in self.order_line:
            rec.estimated_estimated_amountqty = round(rec.product_qty, 6)
            rec.estimated_amount = round(rec.price_total, 6)

    @api.multi
    def act_validate(self):
        self.write({'state': 'done'})
        location_dest_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('location_id.name', '=', 'Installation'),
             ('name', '=', 'Done')], limit=1)
        location_from_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('location_id.name', '=', 'Installation'),
             ('name', '=', 'Pending')], limit=1)


class OrderLine(models.Model):
    _inherit = 'purchase.order.line'

    date_plan = fields.Datetime(string='Scheduled Date', compute='_compute_date_plan', required=True, index=True)

    panel_line_id = fields.Many2one('tokiku.panel_line', string='Panel')
    panel_id = fields.Many2one('tokiku.panel', string='Assembly Panel')
    assembly_po_id = fields.Many2one('purchase.order')

    contract_id = fields.Many2one(related='order_id.contract_id', string='Contract')
    part_no = fields.Char(related='product_id.code', string='Product Number')
    supplier_name = fields.Char(related='order_id.partner_id.ref', readonly=True, string='Supplier')
    supplier_part_no = fields.Char(string='Supplier Part Number', related='product_id.supplier_part_no', readonly=True)
    part_no = fields.Char(related='product_id.part_no')
    default_code = fields.Char(readonly=True)  # related='product_id.default_code',
    description = fields.Char(string='Specification', readonly=True)
    seller_id = fields.Many2one('product.supplierinfo', string='Supplier', compute='_compute_seller_id', store=True)

    prod_categ_id = fields.Many2one('product.category', string='Item')

    mold_id = fields.Many2one('product.product', string='Mold', related='product_id.mold_id')
    mold_seller_id = fields.Many2one('res.partner', string='Mold Seller')
    mold_supplier_part_no = fields.Char(string='Supplier Part Number', related='panel_line_id.mold_supplier_part_no', store=True)
    mold_material = fields.Char(related='panel_line_id.mold_material', store=True)
    mold_weight = fields.Float('Weight', related='panel_line_id.mold_weight', store=True)  # , store=True

    material = fields.Char('Material')  # related='product_id.name',
    net_weight = fields.Float('Weight',
                              compute='_compute_weight')  # product.weight  # related='product_id.weight', readonly=True
    order_length = fields.Float('Order Length')  # related='product_id.volume'
    order_weight = fields.Float('Order Weight', compute='_compute_order_weight', store=True)
    order_width = fields.Float('Order Width')
    order_category = fields.Char('Order Category', related='order_id.po_category_id.name')
    mold_part_ids_name = fields.Char('Mold Part Desc')  # , compute='_compute_mold_part_desc'

    demand_id = fields.Many2one('tokiku.demand', string='Demand')
    demand_qty = fields.Integer('Demand Quantity')  # 需求量

    order_qty = fields.Integer(string='Order Quantity')  # 下訂量
    spare_qty = fields.Integer(string='Spare Quantity')
    qty_normal = fields.Integer(string='Order Quantity', compute='_compute_order_qty')
    qty_back_order = fields.Integer(string='Back Order Quantity', compute='_compute_order_qty')
    user_customized_price_unit = fields.Many2one('tokiku.user_customized_price_unit',
                                                 string="User Customized Price Unit")
    processing_atlas = fields.Char(readonly=True)
    min_qty = fields.Float(related='product_id.min_qty', readonly=True)
    ingot = fields.Char(related='panel_line_id.seller_id.ingot', store=True)
    project_id = fields.Many2one(related='product_id.project_id', store=True)
    estimated_amount = fields.Float(string='Estimated amount', store=True, digits=(16, 6))  # 預估金額
    estimated_qty = fields.Float(string='Estimated Quantity', store=True, digits=(16, 6))  # 預估數量

    rest_demand_qty = fields.Integer('Rest Order Qty')
    rest_demand_weight = fields.Float('Rest Order Weight')

    # For mold
    price_per_set = fields.Float('Price Per Set', compute='_compute_price_per_set')  # 單價/組 (computed)
    price_sum = fields.Float('Price Sum', compute='_compute_price_sum')
    mold_expected_arrival_date = fields.Char('Mold Exp Arrival Date',
                                             related='panel_line_id.mold_expected_arrival_date')

    material_expected_delivery_date = fields.Char('Material Exp Delivery Date',
                                                  related='panel_line_id.material_expected_delivery_date')
    remark = fields.Char('Remark', default='')
    special_type = fields.Char('Special Type')
    mold_line = fields.Many2one('tokiku.mold_line', compute='_compute_mold_line', store=True)

    atlas_id = fields.Many2one('tokiku.atlas', string='Processing Atlas')  # 加工圖集
    atlas_short = fields.Char('atlas short name', related='atlas_id.short_name')
    surface_coating = fields.Char('Surface Coating')  # related='product_id.surface_coating'
    color_code = fields.Char('Color Code')  # related='product_id.color_code'
    cutting_length = fields.Float('Cutting Length')
    cutting_width = fields.Float('Cutting Width')
    code = fields.Char()

    atlas_description = fields.Char('Atlas Description')

    unit_area = fields.Float('Unit Area', compute='_compute_unit_area', store=True)
    estimated_delivery_date = fields.Char('Estimated Delivery Date', default='')

    raw_pricing_single_weight = fields.Float('Pricing Single Weight', compute='_compute_single_weight')
    raw_pricing_total_weight = fields.Float('Pricing Total Weight', compute='_compute_total_weight')

    # unit_weight 就是鋁擠型單位重，由供應商來
    unit_weight = fields.Float('Unit Weight', compute='_compute_unit_weight', store=True)
    refine_weight = fields.Float('Unit Weight')
    refine_pricing_single_weight = fields.Float('Single Weight', compute='_compute_refine_single_weight')
    refine_pricing_total_weight = fields.Float('Total Weight', compute='_compute_refine_single_weight')

    # 烤漆訂製單細項:
    unit_paint_area = fields.Float('Unit Paint Area', compute='_compute_unit_paint_area', store=True)
    paint_area = fields.Float('Paint Area', compute='_compute_paint_area', store=True)
    surface_coating_qty = fields.Float('Surface Coating Qty', related='product_qty')
    unit = fields.Char('Unit')

    single_weight = fields.Float('Single Weight')
    total_weight = fields.Float('Total Weight', compute='_compute_total_weight')

    price_unit_pcs = fields.Float('Price Unit Pcs')
    # price_unit_jp = fields.Float('Price Unit JP')

    valuation_price = fields.Float('Valuation Price')
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),
                               compute='_compute_order_qty', store=True, default=0.0)  # compute='_compute_product_qty'
    total_ordered_qty = fields.Integer('Ordered Qty')
    qty_not_received = fields.Float(compute='_compute_qty_not_received', string="Not Received Qty")
    received_weight = fields.Float(compute='_compute_received_weight', string="Received Weight")
    not_received_weight = fields.Float(compute='_compute_received_weight', string="Not Received Weight")
    received_area = fields.Float(compute='_compute_received_weight', string="Received Area")
    not_received_area = fields.Float(compute='_compute_received_weight', string="Not Received Area")
    left_qty = fields.Float(string='Left Over Qty', compute='_compute_qty_not_received', store=True)
    panel_categ_code = fields.Char(string='Panel_Categ_Code', compute='_compute_panel_categ_code')

    # for order panel use:
    order_id = fields.Many2one('purchase.order')
    stage = fields.Char('Stage', compute='_compute_process_categ', store=True)
    stage_code = fields.Char(compute='_compute_process_categ', store=True)

    # for aluminum order panel use:
    alumi_received_weight = fields.Float(compute='_compute_received_weight', string="Received Weight")
    alumi_not_received_weight = fields.Float(compute='_compute_received_weight', string="Not Received Weight")
    building = fields.Char(string='Building', related='atlas_id.building')
    bom_no = fields.Many2one('tokiku.atlas', string='BOM Number')

    # for assembly purchase order use:
    bom_id = fields.Many2one('mrp.bom', string='BOM Number')  # 組合編號
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別
    factory_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory')  # 組裝廠
    product_code = fields.Char(string='Product Code')  # 產品編號
    single_surface = fields.Float(string='Single Surface')  # 單一面積
    unit_price = fields.Float(string='Unit Price', digits=(6, 2))  # 單價
    # value_unit = fields.Float(string='Value Unit')  # 計價單位
    total_surface_qty = fields.Float(string='Total Surface Qty',
                                     compute='_compute_total_surface_qty')  # 總數量(面積) (computed)
    assembly_pps = fields.Float(string='Price Per Set', compute='_compute_assembly_pps')  # 單價/組
    total = fields.Float(string='Total', compute='_compute_total')  # 合計 (computed)
    material_total = fields.Float(string='Material Total')
    paint_unit_prices = fields.Float(string='Paint Unit Price', digits=(6, 2))
    material_unit_prices = fields.Float(string='Material Unit Price', digits=(6, 2))

    # for installation purchase order use:
    # install_categ = fields.Many2one('product.category', string='Install Category', related='') # 安裝類別
    install_loc = fields.Many2one('tokiku.install_location', string='Install Location')  # 區域位置
    install_categ = fields.Many2one('tokiku.installation_category', string='Install Category')
    install_panel_line_id = fields.Many2one('tokiku.installation_panel_line', string='Install Panel')
    floor = fields.Char(string='Floor')  # 樓層
    product_categ = fields.Char(string='product categ')

    # for installation valuation use:
    atlas_name = fields.Char(string='Processing Atlas')  # 加工圖集
    installed_qty = fields.Integer(string='Installed Qty')  # 已安裝數
    installed_surface = fields.Integer(string='Installed Surface')  # 已安裝面積
    valuation_qty = fields.Integer(string='Valuation Qty')  # 計價數量
    valuation_area = fields.Float(string='Valuation Area')  # 計價面積

    @api.multi
    def _compute_panel_categ_code(self):
        for rec in self:
            for line in rec.project_id.estimate_ids:
                if line.product_categ_id.id == rec.order_id.categ_id.id:
                    rec.panel_categ_code = str(rec.order_id.categ_id.name) + "($" + str(line.estimate_amount) + ")"


    # line.product_categ_id,

    @api.multi
    @api.depends('order_length', 'order_width')
    def _compute_unit_area(self):
        for rec in self:
            rec.unit_area = round(rec.order_length / 1000 * rec.order_width / 1000, 3)
            # print rec.unit_area

    @api.multi
    @api.depends('order_qty', 'single_surface')
    def _compute_total_surface_qty(self):
        for rec in self:
            rec.total_surface_qty = rec.order_qty * rec.single_surface

    @api.multi
    @api.depends('single_surface', 'unit_price')
    def _compute_assembly_pps(self):
        for rec in self:
            rec.assembly_pps = rec.single_surface * rec.unit_price

    @api.multi
    @api.depends('order_qty', 'assembly_pps')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.order_qty * rec.assembly_pps

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            for val in line._prepare_stock_moves(picking):
                val.update({
                    'panel_line_id': line.panel_line_id.id
                })
                done += moves.create(val)
        return done

    @api.multi
    @api.depends('order_id.stage')
    def _compute_process_categ(self):
        for rec in self:
            # rec.stage = rec.order_id.stage
            rec.stage = dict(rec.order_id._fields['stage'].selection).get(rec.order_id.stage)
            rec.stage_code = rec.order_id.stage

    # @api.multi
    # @api.depends('order_id.stage')
    # def _compute_stage_code(self):
    #     for rec in self:
    #         rec.stage_code = rec.order_id.stage
    #         # rec.stage = dict(rec.order_id._fields['stage'].selection).get(rec.order_id.stage)

    @api.multi
    @api.depends('spare_qty', 'order_qty')
    def _compute_order_qty(self):
        for rec in self:
            if rec.order_id.po_category_id.code == 'back':
                rec.qty_normal = 0
                rec.qty_back_order = rec.order_qty
            else:
                rec.qty_normal = rec.order_qty
                rec.qty_back_order = 0

            rec.product_qty = rec.order_qty + rec.spare_qty

    # @api.multi
    # @api.depends('spare_qty', 'order_qty')
    # def _compute_product_qty(self):
    #     for rec in self:
    #         rec.product_qty = rec.order_qty + rec.spare_qty

    @api.multi
    @api.depends('product_qty', 'qty_received')
    def _compute_qty_not_received(self):
        for rec in self:
            rec.qty_not_received = rec.product_qty - rec.qty_received
            rec.left_qty = rec.product_qty - rec.qty_received

    @api.multi
    @api.depends('net_weight', 'product_qty')
    def _compute_order_weight(self):
        for rec in self:
            if rec.order_id.categ_id.code == 'aluminum':
                rec.order_weight = rec.product_qty * rec.unit_weight * (rec.order_length / 1000.0)

    @api.multi
    @api.depends('qty_received', 'product_qty')
    def _compute_received_weight(self):
        for rec in self:
            rec.received_weight = round(int(rec.qty_received) * rec.net_weight * (rec.order_length / 1000.0), 3)
            rec.not_received_weight = round(int(rec.qty_not_received) * rec.net_weight * (rec.order_length / 1000.0), 3)
            rec.alumi_received_weight = round(int(rec.qty_received) * rec.unit_weight * (rec.order_length / 1000.0), 3)
            rec.alumi_not_received_weight = round(
                int(rec.qty_not_received) * rec.unit_weight * (rec.order_length / 1000.0), 3)
            rec.received_area = round(int(rec.qty_received) * rec.paint_area, 3)

    # @api.multi
    # @api.depends('qty_not_received', 'product_qty')
    # def _compute_not_received_weight(self):
    #     for rec in self:
    #         rec.not_received_weight = round(int(rec.qty_not_received) * rec.net_weight * (rec.order_length / 1000.0), 3)
    #
    # @api.multi
    # @api.depends('qty_received', 'product_qty')
    # def _compute_alumi_received_weight(self):
    #     for rec in self:
    #         rec.alumi_received_weight = round(int(rec.qty_received) * rec.unit_weight * (rec.order_length / 1000.0), 3)
    #
    # @api.multi
    # @api.depends('qty_not_received', 'product_qty')
    # def _compute_alumi_not_received_weight(self):
    #     for rec in self:
    #         rec.alumi_not_received_weight = round(
    #             int(rec.qty_not_received) * rec.unit_weight * (rec.order_length / 1000.0), 3)
    #
    # @api.multi
    # @api.depends('qty_received', 'product_qty')
    # def _compute_received_area(self):
    #     for rec in self:
    #         rec.received_area = round(int(rec.qty_received) * rec.paint_area, 3)
    #
    # @api.multi
    # @api.depends('qty_not_received', 'product_qty')
    # def _compute_not_received_area(self):
    #     for rec in self:
    #         rec.not_received_area = round(int(rec.qty_not_received) * rec.unit_area, 3)

    @api.multi
    @api.depends('single_weight')
    def _compute_total_weight(self):
        for rec in self:
            rec.total_weight = rec.single_weight * rec.product_qty

    @api.multi
    @api.depends('mold_id.paint_area')
    def _compute_unit_paint_area(self):
        for rec in self:
            rec.unit_paint_area = rec.panel_line_id.mold_id.paint_area

    @api.multi
    @api.depends('unit_paint_area', 'order_length', 'order_qty')
    def _compute_paint_area(self):
        for rec in self:
            if rec.order_qty > 0:
                rec.paint_area = round((rec.unit_paint_area * rec.order_length) / 1000000 * rec.order_qty, 6)

    @api.multi
    # @api.depends('product_qty', 'price_per_set')
    def _compute_mold_line(self):
        for rec in self:
            mold_line = self.env['tokiku.mold_line'].search(
                [('product_id', '=', rec.product_id.id)])
            if mold_line and len(mold_line) == 1:
                rec.mold_line = mold_line[0]

    @api.multi
    @api.depends('product_qty', 'price_per_set')
    def _compute_price_sum(self):
        for rec in self:
            rec.price_sum = round(rec.price_per_set * rec.product_qty, 3)

    @api.multi
    @api.depends('product_qty', 'product_id', 'price_unit', 'price_total')
    def _compute_price_per_set(self):
        for rec in self:
            if rec.product_id.category_code == 'mold':
                mold_part = self.env['tokiku.mold_part'].search(
                    [('product_id', '=', rec.product_id.id)])
                if len(mold_part) > 0:
                    for m in mold_part:
                        if m.project_id.id == self.env.user.project_id.id:
                            rec.price_per_set += m.price
                            rec.price_unit += m.price
                            rec.price_total += m.price

    @api.multi
    @api.depends('supplier_name')
    def _compute_seller_id(self):
        for rec in self:
            seller = self.env['product.supplierinfo'].search(
                [('product_id', '=', rec.product_id.id), ('supplier_name', '=', rec.supplier_name)])

            if seller and len(seller) == 1:
                rec.seller_id = seller[0]

    # @api.multi
    # def _compute_mold_part_desc(self):
    #     for rec in self:
    #         mold_part = self.env['tokiku.mold_part'].search([
    #             ('product_part_no', '=', rec.default_code)
    #         ])
    #         rec.mold_part_ids_name = ', '.join([s.name.name for s in mold_part])

    @api.multi
    def _compute_weight(self):
        for rec in self:
            rec.net_weight = rec.product_id.weight

    @api.multi
    @api.depends('supplier_name', 'order_id', 'product_id', 'product_qty')
    def _compute_unit_weight(self):
        for rec in self:
            if rec.order_id.stage == 'material':
                # sellers = rec.product_id.mold_id.seller_ids.filtered(lambda x: x.product_material == rec.material and x.name.id == rec.order_id.partner_id.id)
                sellers = rec.product_id.mold_id.seller_ids.filtered(lambda x: x.product_material == rec.material)
                for s in sellers:
                    rec.unit_weight = s.weight
                    # print ("s.weight %s" % s.weight)
                    break
            else:
                sellers = rec.panel_line_id.mold_id.seller_ids
                # sellers = rec.panel_line_id.mold_id.seller_ids.filtered(
                #     lambda x: x.product_material == rec.material and x.name.id == rec.mold_seller_id.id)

                for s in sellers:
                    rec.unit_weight = s.weight
                    # print ("s.weight %s" % s.weight)
                    break

                    # rec.unit_paint_area = rec.mold_id.paint_area
                    # print ("rec.unit_paint_area %s" % rec.unit_paint_area)
            # if rec.order_id.stage == 'material':
            #     mold = self.env['product.product'].sudo().search([('category_code', '=', 'mold'),
            #                                                       ('default_code', '=', rec.code),
            #                                                       ], limit=1)
            # else:
            #     mold = self.env['product.product'].sudo().search([('category_code', '=', 'mold'),
            #                                                       ('default_code', '=', rec.code),
            #                                                       ], limit=1)

            # sellers = rec.mold_id.seller_ids.filtered(
            #     lambda x: x.product_material == rec.material and
            #               x.name.id == rec.order_id.partner_id.id)
            # print ("sellers %s" % sellers)
            #
            # for s in sellers:
            #     rec.unit_weight = s.weight
            #     print ("s.weight %s" % s.weight)
            #
            #     break

    @api.onchange('demand_qty', 'spare_qty')
    def _onchange_qty(self):
        if not self.product_id:
            return
        self.product_qty = self.demand_qty + self.spare_qty
        self._get_seller_price()

    @api.onchange('product_qty')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        if self.product_qty < self.demand_qty:
            self.demand_qty = self.product_qty
            self.spare_qty = 0
        else:
            self.spare_qty = self.product_qty - self.demand_qty
        self._get_seller_price()

    def _get_seller_price(self):
        seller = self.product_id.seller_ids.filtered(lambda x: x.name.id == self.partner_id.id)
        if not seller:
            return

        if self.order_id.categ_id.code == 'raw':
            self.price_unit = self.product_id.product_tmpl_id.market_price * self.product_id.volume / 1000 * self.product_id.weight
        else:
            self.price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                                                                              self.product_id.supplier_taxes_id,
                                                                              self.taxes_id) if seller else 0.0

    @api.onchange('product_id')
    def onchange_product_id(self):
        project_id = self.env.user.project_id.id or self.project_id.id
        contract_id = self.env.user.contract_id.id or self.contract_id.id

        if not self.order_id.categ_id:
            product_lang = self.product_id.with_context({
                'lang': self.partner_id.lang,
                'partner_id': self.partner_id.id,
                'project_id': project_id,
                'contract_id': contract_id,
            })
            self.name = product_lang.name
            if product_lang.description_purchase:
                self.name += '\n' + product_lang.description_purchase
            self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
            self.date_planned = fields.datetime.now()

            return {}

        project_id = self.env.user.project_id.id or self.project_id.id

        panel = self.env['tokiku.panel'].with_context(project_id=project_id).search(
            [('project_id', '=', project_id), ('categ_id', '=', self.order_id.categ_id.id)])
        # contract_id = self.env.user.contract_id.id or self.contract_id.id
        # if self.order_id.categ_id.code == 'mold' or self.order_id.categ_id.code == 'raw':
        #     panel = self.env['tokiku.panel'].with_context(project_id=project_id).search(
        #                 [('project_id', '=', project_id), ('categ_id', '=', self.order_id.categ_id.id)])
        # else:
        #     panel = self.env['tokiku.panel'].with_context(contract_id=contract_id).search(
        #         [('contract_id', '=', contract_id), ('categ_id', '=', self.order_id.categ_id.id)])

        result = {}
        if not self.product_id:
            return result

        self._suggest_quantity()
        self._onchange_quantity()

        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
            'project_id': self.order_id.project_id.id,
            'contract_id': self.order_id.contract_id.id,
        })
        self.name = product_lang.name
        if product_lang.description_purchase:
            self.name += '\n' + product_lang.description_purchase

        fpos = self.order_id.fiscal_position_id
        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id
            self.taxes_id = fpos.map_tax(
                self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
        else:
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)

        panel_line = panel.line_ids.filtered(lambda x: x.product_id.id == self.product_id.id)
        if panel_line:
            self.demand_qty = panel_line.rest_demand_qty
            self.product_qty = panel_line.rest_demand_qty
            seller = self.product_id.seller_ids.filtered(lambda x: x.name.id == self.partner_id.id)
            self.price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                                                                              panel_line.product_id.supplier_taxes_id,
                                                                              panel_line.product_id.supplier_taxes_id)
            self._get_seller_price()
        else:
            self.price_unit = self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        self.date_planned = fields.datetime.now()

        return result

    @api.multi
    @api.depends('product_id', 'order_length', 'product_qty')
    def _compute_single_weight(self):
        for rec in self:
            rec.raw_pricing_single_weight = round(rec.product_id.weight * (rec.order_length / 1000.0), 6)
            rec.raw_pricing_total_weight = round(rec.product_qty * rec.product_id.weight * (rec.order_length / 1000.0),
                                                 6)

    # @api.multi
    # @api.depends('product_qty', 'product_id', 'order_length')
    # def _compute_total_weight(self):
    #     for rec in self:
    #         rec.raw_pricing_total_weight = round(rec.product_qty * rec.product_id.weight * (rec.order_length / 1000.0),
    #                                              6)

    @api.multi
    @api.depends('unit_weight', 'order_length', 'product_qty')
    def _compute_refine_single_weight(self):
        for rec in self:
            rec.refine_pricing_single_weight = round((rec.unit_weight * rec.order_length) / 1000.0, 6)
            if rec.order_qty > 0:
                rec.refine_pricing_total_weight = round(rec.unit_weight * (rec.order_length / 1000.0) * rec.product_qty,
                                                        6)

    # @api.multi
    # @api.depends('unit_weight', 'product_qty', 'order_length')
    # def _compute_refine_total_weight(self):
    #     for rec in self:
    #         if rec.order_qty > 0:
    #             rec.refine_pricing_total_weight = round(rec.unit_weight * (rec.order_length / 1000.0) * rec.product_qty,
    #                                                     6)

    # @api.depends('date_plan')
    def _compute_date_plan(self):
        fmt = '%Y-%m-%d %H:%M:%S'
        user_time_zone = pytz.UTC

        if self.env.user.partner_id.tz:
            user_time_zone = pytz.timezone(self.env.user.partner_id.tz)

        for rec in self:
            user_time = datetime.strptime(rec.date_order, fmt)
            user_time = pytz.utc.localize(user_time).astimezone(user_time_zone)
            rec.date_plan = user_time.strftime(fmt)

    @api.depends('invoice_lines.invoice_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.invoice_id.state not in ['cancel']:
                    if inv_line.invoice_id.type == 'in_invoice':
                        qty += inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                    elif inv_line.invoice_id.type == 'in_refund':
                        qty -= inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.qty_invoiced = qty


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    categ_id = fields.Many2one('product.category', 'Category')
    tokiku_project_id = fields.Many2one('project.project', string='Project')
    contract_ids = fields.One2many('account.analytic.contract', 'sale_order_id', string='Contract')

    @api.multi
    def open_sale_order(self):
        if not self.env.user.contract_id:
            raise UserError(_('Please select a contract first!'))
            return

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_sale_order_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_sale_order_form')[1]
        return {
            'name': _('Sale Order'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('tokiku_project_id', '=', self.env.user.project_id.id)],
            'context': {
                'default_tokiku_project_id': self.env.user.project_id.id,
                'default_contract_id': self.env.user.contract_id.id,
                'customer_ids': [c.customer_id.id for c in self.env.user.project_id.customer_info_ids],
                'contract_ids': [c.id for c in self.env.user.project_id.contract_ids],
            }
        }

    @api.onchange('tokiku_project_id')
    def _onchange_categ_id(self):
        if self.tokiku_project_id:
            ci = self.tokiku_project_id.contract_ids
            if ci:
                return {'domain': {'contract_id': [('id', 'in', [c.id for c in ci])]}}

        return {}
