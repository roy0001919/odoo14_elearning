# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

import pytz

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InstallationDemand(models.Model):
    _name = 'tokiku.installation_demand'

    categ_id = fields.Many2one('product.category', 'Category')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')  # 合約
    project_id = fields.Many2one('project.project', string='Project')  # 專案
    file_date = fields.Datetime(string='File Date', readonly=True, index=True, default=fields.Datetime.now)  # 製單日期

    installation_demand_line_ids = fields.One2many('tokiku.install_demand_line', 'installation_demand_id')

    building_id = fields.Many2one('tokiku.building', string='Building',
                                  required=True)  # 棟別 for installation demand form
    name = fields.Char('Demand Form Number', required=True, readonly=True, index=True, copy=False,
                       default='New')  # 需求單號
    demand_location = fields.Char('Demand Location')  # 需求位置

    atlas_name = fields.Char(string='Atlas', required=True)  # 加工圖集
    install_categ_id = fields.Many2one('tokiku.installation_category', string='Install Category', required=True)  # 安裝類別
    install_loc_id = fields.Many2one('tokiku.install_location', string='Install Location', required=True)  # 區域位置

    install_date = fields.Char(string='Install Date')  # 安裝日期

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
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tokiku.installation_demand') or '/'

        return super(InstallationDemand, self).create(vals)

    @api.multi
    def act_import(self):
        project_id = self.env.user.project_id
        assembly_id = self.env['product.category'].search(
            [('code', '=', 'installation_assembly')])
        processing_id = self.env['product.category'].search(
            [('code', '=', 'installation_processing')])
        categ = self.env['product.category'].sudo().search([('code', '=', 'installation')])
        product_categ = processing_id
        for d in self:
            panel_id = self.env['tokiku.panel'].search(
                [('project_id', '=', project_id.id), ('categ_id', '=', categ.id)])
            for l in d.installation_demand_line_ids:
                if l.product_categ == 'Installation Assembly':
                    product_categ = assembly_id

                product = self.env['product.product'].sudo().search(
                    [('project_id', '=', project_id.id),
                     ('default_code', '=', l.default_code),  # this field is tokiku default code.
                     ('categ_id', '=', product_categ.id),
                     ])

                if not product:
                    product = self.env['product.product'].create({
                        'project_id': project_id.id,
                        'default_code': l.default_code,
                        'categ_id': product_categ.id,
                        'name': l.default_code,
                    })

                pl = panel_id.installation_panel_line_ids.filtered(lambda
                                                                       x: x.product_id.id == product.id
                                                                       and x.floor == l.floor
                                                                       and x.atlas_name == d.atlas_name
                                                                       and x.product_categ == l.product_categ
                                                                       and x.building_id.id == d.building_id.id
                                                                       and x.install_categ_id.id == d.install_categ_id.id
                                                                       and x.install_loc_id.id == d.install_loc_id.id)

                if not pl:
                    panel_id.sudo().installation_panel_line_ids = [(0, 0, {'product_id': product.id,
                                                                           'default_code': product.default_code,
                                                                           'product_categ': l.product_categ,
                                                                           'length': l.length,
                                                                           'width': l.width,
                                                                           'single_surface': l.single_surface,
                                                                           'floor': l.floor,
                                                                           'demand_qty': l.demand_qty,
                                                                           'total_surface': l.total_surface,
                                                                           'atlas_name': d.atlas_name,
                                                                           'building_id': d.building_id.id,
                                                                           'install_categ_id': d.install_categ_id.id,
                                                                           'install_loc_id': d.install_loc_id.id,
                                                                           'demand_id': d.id,
                                                                           'project_id': self.env.user.project_id.id,
                                                                           'categ_id': product_categ.id,

                                                                           })]
                else:
                    pl.demand_qty += l.demand_qty

            panel_id.sudo().installation_panel_line_ids._compute_rest_demand_qty()
            panel_id.sudo().installation_panel_line_ids._compute_uninstalled_qty()


class InstallationDemandLine(models.Model):
    _name = 'tokiku.install_demand_line'

    installation_demand_id = fields.Many2one('tokiku.installation_demand', string='Demand', ondelete='cascade')
    # atlas_name = fields.Char(string='Processing Atlas')  # 加工圖集
    install_categ = fields.Many2one('product.category', string='Install Category')  # 安裝類別
    install_loc = fields.Many2one('tokiku.install_location', string='Install Location')  # 區域位置
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別 for installation demand form
    demand_form_num = fields.Char('Demand Form Number', required=True, readonly=True, index=True, copy=False,
                                  default='New')  # 需求單號

    product_categ = fields.Char(string='Product Category', default='加工產品')  # 產品類別
    default_code = fields.Char(string='Processing Number')  # 產品編號
    # bom_id = fields.Many2one('mrp.bom', string='BOM Number')  # 組合編號
    length = fields.Float(string='Length')  # 長度
    width = fields.Float(string='Width')  # 寬度
    single_surface = fields.Float(string='Single Surface')# , compute='_compute_single_surface', store=True)  # 單一面積
    floor = fields.Char(string='Floor')  # 樓層
    demand_qty = fields.Integer(string='Demand Qty')  # 需求數
    # total_demand = fields.Integer(string='Total Demand')  # 總需求數
    total_surface = fields.Float(string='Total Surface', compute='_compute_total_surface', store=True)  # 總面積
    # value_unit = fields.Char('Value Unit')  # 計價單位

    # @api.multi
    # @api.depends('length', 'width', 'value_unit')
    # def _compute_single_surface(self):
    #     for rec in self:
    #         if rec.value_unit == "m2":
    #             rec.single_surface = (rec.length * rec.width) / 1000000
    #         elif rec.value_unit == "m":
    #             rec.single_surface = (rec.length * rec.width) / 1000
    #         else:
    #             rec.single_surface = rec.length * rec.width

    @api.multi
    @api.depends('demand_qty', 'single_surface')
    def _compute_total_surface(self):
        for rec in self:
            rec.total_surface = rec.demand_qty * rec.single_surface


class InstallationPanelLine(models.Model):
    _name = 'tokiku.installation_panel_line'

    categ_id = fields.Many2one('product.category', 'Category')
    project_id = fields.Many2one('project.project', string='Project')  # 專案
    panel_id = fields.Many2one('tokiku.panel', string='Panel')  # Reference to Panel Class
    demand_id = fields.Many2one('tokiku.installation_demand', string='Demand')  # Relation with demand panel
    order_line_ids = fields.One2many('purchase.order.line', 'install_panel_line_id', string='Order Lines',
                                     delete='cascade')

    atlas_name = fields.Char(string='Processing Atlas')  # 加工圖集
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別 for installation demand form
    install_categ_id = fields.Many2one('tokiku.installation_category', string='Install Category')  # 安裝類別
    install_loc_id = fields.Many2one('tokiku.install_location', string='Install Location')  # 區域位置
    default_code = fields.Char(related='product_id.default_code', string='Processing Number', store=True)  # 加工編號
    demand_qty = fields.Integer(string='Demand Qty')  # 需求數
    order_qty = fields.Integer(string='Order Quantity', compute='_compute_order_qty')  # 下訂量
    rest_demand_qty = fields.Integer(string='Rest Demand Quantity', compute='_compute_rest_demand_qty')  # 未下訂量
    product_categ = fields.Char(string='product categ')

    # source_supplier = fields.Many2one('res.partner', string='Source Supplier')  # 來源供應商
    # target_supplier = fields.Many2one('res.partner', string='Target Supplier')  # 目的供應商
    demand_form_num = fields.Char('Demand Form Number', required=True, readonly=True, index=True, copy=False,
                                  default='New')  # 需求單號

    product_id = fields.Many2one('product.product', string='Product')  # default_code use
    length = fields.Float(string='Length')  # 長度
    width = fields.Float(string='Width')  # 寬度
    single_surface = fields.Float(string='Single Surface')  # 單一面積
    floor = fields.Char(string='Floor')  # 樓層
    total_surface = fields.Float(string='Total Surface')  # 總面積
    # value_unit = fields.Char('Value Unit')  # 計價單位 (Ref. Paint Order)
    production_record_line_ids = fields.One2many('tokiku.inst_prodrec_line', 'installation_panel_line_id')

    feed_total_qty = fields.Integer(string='Feed Total Qty', compute='_compute_qty_done', store=True)  # 進料合計數(工地庫存)
    unfed_qty = fields.Integer(string='Unfed Qty', compute='_compute_unfed_qty')  # 未進料(demand_qty - feeding_total_qty)
    done_uninstalled_qty = fields.Integer(string='Done Uninstall', compute='_compute_qty_done', store=True)
    fed_surface = fields.Integer(string='Fed Surface', compute='_compute_qty_done', store=True)  # 已進料面積

    # 已安裝計價單
    installed_qty = fields.Integer(string='Installed Qty', compute='_compute_installed_qty', store=True)  # 已安裝數
    installed_surface = fields.Integer(string='Installed Surface', compute='_compute_installed_qty',
                                       store=True)  # 已安裝面積
    uninstalled_qty = fields.Integer(string='Uninstall Qty', compute='_compute_installed_qty', store=True)  # 未安裝數量

    incoming_install = fields.Char(string='Incoming installation', compute='_compute_percent_qty')#, store=True)  # 進料安裝%(已安裝/進料數)
    demand_install = fields.Char(string='Demand install pct', compute='_compute_percent_qty')#, store=True)# 總需求安裝%(已安裝/需求數)
    lack_install = fields.Char(string='Lack stuff', compute='_compute_percent_qty')#, store=True)# 缺料%(未進料/需求)
    incoming_demand = fields.Char(string='Incoming Demand', compute='_compute_percent_qty')#, store=True)# 進料%(進料/需求)
    # 退貨合計數
    return_qty = fields.Integer(string='Return Qty')

    # valuation_qty = fields.Integer(string='Valuation Qty')  # 計價數量
    # valuation_area = fields.Float(string='Valuation Area')  # 計價面積
    @api.multi
    def act_unfed_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_installation_unfed_qty')[1]
        location_dest_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('name', '=', 'Stock')])
        # [('usage', '=', 'internal'),
        #  ('location_id.name', '=', 'Installation'),
        #  ('name', '=', 'Pending')])

        return {
            'name': "Unfed Qty Done",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [('location_dest_id', '=', location_dest_id.id),
                       ('install_atlas', '=', self.atlas_name),
                       ('new_default_code', '=', self.default_code),
                       ('product_id', '=', self.product_id.id),
                       ],
        }

    @api.multi
    def act_install_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_installation_install_qty')[1]
        location_dest_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('location_id.name', '=', 'Installation'),
             ('name', '=', 'Done')])

        return {
            'name': "Install Qty Done",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [('install_atlas', '=', self.atlas_name),
                       ('default_code', '=', self.default_code),
                       ('location_dest_id', '=', location_dest_id.id),
                       ('product_id', '=', self.product_id.id),
                       ],
        }

    @api.multi
    def act_order_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_installation_order_qty')[1]
        return {
            'name': "Order Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order.line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            # 'flags': {'tree': {'headless': False}},
            'domain': [('install_panel_line_id', '=', self.id),
                       ('stage_code', '=', 'installation'),
                       ('state', '=', 'purchase'),
                       ],
            # 'context': {'search_default_groupby_supplier': 1},
        }
    @api.multi
    def _compute_uninstalled_qty(self):
        for rec in self:
            rec.uninstalled_qty = rec.demand_qty - rec.installed_qty

    @api.multi
    def _compute_rest_demand_qty(self):
        for rec in self:
            rec.rest_demand_qty = rec.demand_qty - rec.order_qty

    @api.multi
    def _compute_order_qty(self):
        for rec in self:
            for l in rec.order_line_ids.filtered(lambda x: x.state in ['purchase', 'done']):
                rec.order_qty = l.order_qty

    @api.multi
    @api.depends('product_id.pack_operation_ids.qty_done')
    def _compute_qty_done(self):
        for rec in self:
            for pick in rec.order_line_ids.order_id.picking_ids:
                for pack in pick.pack_operation_ids:
                    if pack.install_atlas == rec.atlas_name and pack.new_default_code == rec.default_code and pack.floor\
                            == rec.floor:
                        rec.feed_total_qty += pack.qty_done
                        print rec.feed_total_qty
                        rec.fed_surface = rec.feed_total_qty * rec.single_surface
                        rec.done_uninstalled_qty = rec.feed_total_qty - rec.installed_qty

    @api.multi
    def _compute_unfed_qty(self):
        for rec in self:
            rec.unfed_qty = rec.order_qty - rec.feed_total_qty

    @api.multi
    @api.depends('production_record_line_ids.installed_qty')
    def _compute_installed_qty(self):
        for rec in self:
            rec.installed_qty = rec.production_record_line_ids.installed_qty
            rec.uninstalled_qty = rec.demand_qty - rec.installed_qty
            rec.installed_surface = rec.installed_qty * rec.single_surface

    @api.multi
    # @api.depends('installed_qty', 'feed_total_qty', 'demand_qty')
    def _compute_percent_qty(self):
        for rec in self:
            if rec.feed_total_qty != 0 and rec.demand_qty != 0:
                rec.incoming_install = str((rec.installed_qty / rec.feed_total_qty) * 100) + '%'
                rec.demand_install = str((rec.installed_qty / rec.demand_qty) * 100) + '%'
                rec.lack_install = str((rec.unfed_qty / rec.demand_qty) * 100) + '%'
                rec.incoming_demand = str((rec.feed_total_qty / rec.demand_qty) * 100) + '%'
            elif rec.feed_total_qty == 0:
                rec.incoming_install = '0%'
                rec.demand_install = '0%'
                rec.lack_install = '0%'
                rec.incoming_demand = '0%'


class InstallationProdRec(models.Model):
    _name = 'tokiku.inst_prodrec'

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'internal'), ('warehouse_id', '=', False)])
        return types[:1]

    name = fields.Char('Production Record Order Number', required=True, default='New', readonly=True)
    categ_id = fields.Many2one('product.category', 'Category')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    project_id = fields.Many2one('project.project', string='Project')
    inst_prodrec_ids = fields.One2many('tokiku.inst_prodrec_line', 'inst_prodrec_id',
                                       string='Installation Production Record Line')
    # supplier_id = fields.Many2one('tokiku.supplier_info', string='Inst Factory')  # 供應商
    # partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    panel_id = fields.Many2one('tokiku.panel', string='Panel')
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True, default=_default_picking_type)
    picking_id = fields.Many2one('stock.picking')
    source_supplier = fields.Many2one('res.partner', string='Source Supplier', required=True)  # 來源供應商
    target_supplier = fields.Many2one('res.partner', string='Target Supplier', required=True)  # 目的供應商
    install_date = fields.Datetime(string='Install Date', readonly=True, index=True,
                                   default=fields.Datetime.now)  # 安裝日期
    atlas_name = fields.Char(related='inst_prodrec_ids.atlas_name', string='Atlas Name', index=True)

    building_id = fields.Many2one('tokiku.building', string='Building',
                                  required=True)  # 棟別 for installation demand form
    install_loc = fields.Many2one('tokiku.install_location', string='Install Location',
                                  related='inst_prodrec_ids.install_loc')  # 區域位置
    install_categ = fields.Many2one('tokiku.installation_category', string='Install Category',
                                    related='inst_prodrec_ids.install_categ')  # 安裝類別
    # location_from_id = fields.Many2one('stock.location', 'Source Location', default='Pending inst')  # 來源區位
    # location_dest_id = fields.Many2one('stock.location', 'Destination Location', default='Install Done')  # 目的區位
    location_id = fields.Many2one(
        'stock.location', "Source Location Zone",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id, required=True)  # states={'draft': [('readonly', False)]}

    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location Zone",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id, required=True,
    )  # states={'draft': [('readonly', False)]}

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def act_validate(self):
        self.write({
            'state': 'done'
        })
    @api.multi
    def act_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tokiku.inst_prodrec') or '/'
        return super(InstallationProdRec, self).create(vals)

    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
        # self.owner_id = None
        stage = self.env.context.get('default_stage') or self.stage

        if stage:
            project_id = self.env.user.project_id.id or self.project_id.id
            location_name = self.location_dest_id.with_context(lang=None).location_id.name or ''
            if location_name == 'installation':
                location_name = 'Installation'
            supplier_infos = self.env['tokiku.supplier_info'].search(
                [('project_id', '=', project_id),
                 ('prod_catg.code', '=', location_name.lower())])

            return {'domain': {'target_supplier': [('id', 'in', [s.supplier_id.id for s in supplier_infos])]}}

    @api.onchange('location_id')
    def onchange_location_id(self):
        sup_location_ids = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'), ('location_id.name', '=', 'Installation'),
             ('name', 'in', ['Pending', 'Done'])])
        location_dest_ids = [x.id for x in sup_location_ids]

        return {'domain': {'location_dest_id': [('id', 'in', location_dest_ids)]}}

    @api.multi
    def item_select(self):
        self.ensure_one()
        project_id = self.env.context.get('default_project_id')
        panel_id = self.env.context.get('panel_id')

        ctx = {'default_project_id': project_id,
               'panel_id': panel_id,
               'inst_prodrec_id': self.id,
               }
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'inst_record_select_wizard_view')[1]

        return {
            'name': _('Production Record Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.inst_production_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }


class InstallationProdRecLine(models.Model):
    _name = 'tokiku.inst_prodrec_line'

    name = fields.Char(string='Part Number')
    inst_prodrec_id = fields.Many2one('tokiku.inst_prodrec', string='Installation Production Record',
                                      ondelete='cascade')
    installation_panel_line_id = fields.Many2one('tokiku.installation_panel_line', string='Installation Panel Line')
    product_id = fields.Many2one('product.product', string='Product')
    atlas_name = fields.Char(string='Processing Atlas')
    bom_id = fields.Many2one('mrp.bom', string='BOM Number')
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別
    install_loc = fields.Many2one('tokiku.install_location', string='Install Location')  # 區域位置
    install_categ = fields.Many2one('tokiku.installation_category', string='Install Category')  # 安裝類別
    default_code = fields.Char(string='Processing Number')  # 加工編號
    floor = fields.Char(string='Floor')  # 樓層
    feed_total_qty = fields.Integer(string='Total Qty')
    installed_qty = fields.Integer(string='Installed Qty')  # 已安裝數
    installed_surface = fields.Integer(string='Installed Surface')  # 已安裝面積
    state = fields.Char(string='Status', compute='_compute_state')
    pack_operation_id = fields.Many2one('stock.pack.operation')

    @api.onchange('installed_qty')
    def _onchange_installed_qty(self):
        for rec in self:
            if rec.installed_qty > rec.feed_total_qty:
                return {
                    'warning': {
                        'title': 'Wrong quantity',
                        'message': 'Install quantity cannot be greater than the stock quantity',
                    }
                }

    @api.multi
    def _compute_state(self):
        for rec in self:
            for prodrec in rec.inst_prodrec_id:
                rec.state = prodrec.state

