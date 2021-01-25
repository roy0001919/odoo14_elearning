# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

import odoo.addons.decimal_precision as dp
import pytz

from core.biznavi.utils import parse_float
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
doing_cal = False


class Panel(models.Model):
    _name = 'tokiku.panel'

    name = fields.Char(string='Name', compute='_compute_name')
    categ_id = fields.Many2one('product.category', 'Category')
    categ_code = fields.Char(related='categ_id.code')
    project_id = fields.Many2one('project.project', string='Project', delete='cascade', required=True)
    line_ids = fields.One2many('tokiku.panel_line', 'panel_id', string='Panel Lines', delete='cascade')
    assembly_panel_line_ids = fields.One2many('tokiku.assembly_panel_line', 'panel_id', string='Assembly Panel Lines',
                                              delete='cascade')
    atlas_line_ids = fields.One2many('tokiku.atlas_line', 'atlas_id', string='Atlas Line')
    assembly_po_line_ids = fields.One2many('purchase.order.line', 'panel_id', string='Assembly Panel Lines')

    installation_demand_ids = fields.One2many('tokiku.demand_line', 'demand_id', string='Installation Demand')

    order_ids = fields.One2many('purchase.order', 'panel_id', string='Orders', delete='cascade')
    order_line_ids = fields.One2many('purchase.order.line', 'panel_id', string='Order Lines', domain=[('state', 'in', ['purchase', 'done'])])
    installation_panel_line_ids = fields.One2many('tokiku.installation_panel_line', 'panel_id',
                                                  string='Installation Panel Lines',
                                                  delete='cascade')
    install_product_ids = fields.One2many('tokiku.inst_prodrec', 'panel_id', string='Product Record', delete='cascade')

    refresh = fields.Boolean(string='Refresh', default=True)

    @api.multi
    def compute_demand_qty(self):
        for l in self.line_ids:
            l.demand_qty = 0
            headers = {}
            demands = {}
            if l.panel_id.categ_id.code == 'mold':
                l.demand_qty = l.mold_demand_qty
            elif l.panel_id.categ_id.code == 'raw':
                for c in l.panel_id.project_id.contract_ids:
                    for d in c.demand_ids:
                        headers[d.id] = d.name
                        demands[d.id] = 0
                        for dl in d.demand_line_ids.filtered(lambda x: x.product_id.id == l.product_id.id):
                            l.demand_qty += parse_float(dl.qty)
                            demands[d.id] += parse_float(dl.qty)
            else:
                l.demand_qty = l.atlas_demand_qty

    @api.multi
    def calAll(self):
        for panel in self.env['tokiku.panel'].sudo().search([]):
            panel.calculate()

    @api.model
    def docal(self):
        global doing_cal
        for panel in self.env['tokiku.panel'].sudo().search([]):
            doing_cal = True
            panel.calculate()
            doing_cal = False

    # @api.multi
    # def cal_order(self):
    #     for panel in self:
    #         start_time = datetime.now()
    #         print('calculate order %s ==> %s' % (panel.project_id.id, panel.id))
    #         # panel._compute_order_line_ids()
    #         # panel.line_ids._compute_order_lines()
    #
    #         # panel.line_ids._compute_demand_qty()
    #         # panel.line_ids._compute_order_qty()
    #         # panel.line_ids._compute_qty_received()
    #         # panel.line_ids._compute_rest_demand_qty()
    #         # panel.line_ids._compute_weight()
    #         # panel.line_ids._compute_weight_sub()
    #         print('calculate order finished in %s' % (datetime.now() - start_time))

    # @api.multi
    # def cal_stock(self):
    #     for panel in self:
    #         start_time = datetime.now()
    #         print('calculate stock %s ==> %s' % (panel.project_id.id, panel.id))
    #         panel.line_ids._compute_paint_qty()
    #         panel.line_ids._compute_cutdone_qty()
    #         panel.line_ids._compute_refined_pending_qty()
    #         panel.line_ids._compute_refined_qty()
    #         panel.line_ids._compute_refine_order_qty()
    #         panel.line_ids._compute_heat_qty()
    #         panel.line_ids._compute_paint_order_qty()
    #         panel.line_ids._compute_heat_order_qty()
    #         print('calculate stock finished in %s' % (datetime.now() - start_time))

    @api.multi
    def calculate(self):
        for panel in self:
            _logger.info('Calculate %s' % panel)
            panel._compute_order_line_ids()
            if len(panel.order_line_ids) > 0:
                panel.line_ids._compute_order_lines()
                panel.line_ids._compute_demand_qty()
                panel.line_ids._compute_order_qty()
                panel.line_ids._compute_qty_received()
                panel.line_ids._compute_rest_demand_qty()
                panel.line_ids._compute_weight()
                panel.line_ids._compute_weight_sub()
                panel.line_ids._compute_paint_qty()
                panel.line_ids._compute_area()
                panel.line_ids._compute_cutdone_qty()
                panel.line_ids._compute_refined_pending_qty()
                panel.line_ids._compute_refined_qty()
                panel.line_ids._compute_refine_order_qty()
                panel.line_ids._compute_heat_qty()
                panel.line_ids._compute_paint_order_qty()
                panel.line_ids._compute_heat_order_qty()
                panel.line_ids._compute_qty_receive_assembly()
                panel.line_ids._compute_qty_receive_site()
                panel.line_ids._compute_percent()
            elif len(panel.assembly_panel_line_ids) > 0:
                panel.assembly_panel_line_ids._compute_completed_prep()
                panel.assembly_panel_line_ids._compute_assembling()
                panel.assembly_panel_line_ids._compute_assembly_qty()
                panel.assembly_panel_line_ids._compute_assembled()
                panel.assembly_panel_line_ids._compute_unassembled()
                panel.assembly_panel_line_ids._compute_incomplete_prep()
                panel.assembly_panel_line_ids._compute_comp_rate()

            panel.refresh = False

    @api.multi
    def _compute_name(self):
        for panel in self:
            panal_type = _(' Panel')
            name = panel.categ_id.name
            if self.env.context.get('panel_type') == 'order':
                panal_type = _(' Order Panel')
            if self.env.context.get('panel_type') == 'dashboard':
                panal_type = ''
            if self.env.context.get('panel_type') == 'assembly_preparation':
                name = _('Assembly Preparation')
            panel.name = "%s%s" % (name, panal_type)

    @api.multi
    @api.depends('order_ids', 'order_ids.state')
    def _compute_order_line_ids(self):
        for rec in self:
            ids = []
            for o in rec.order_ids.filtered(lambda x: x.state in ['purchase', 'done']):
                for l in o.order_line:
                    ids.append(l.id)
            rec.order_line_ids = [(6, 0, ids)]

    def open_material(self):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_material_sum_tree')[1]
        search_view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_line_filter')[1]

        for rec in self.line_ids:
            rec.material_sum_name = "%s/%s" % (rec.material, rec.weight)

        return {
            'name': _('Material List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'tokiku.panel_line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'search_view_id': search_view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'domain': [('panel_id', '=', self.id)],
            'context': {'search_default_material_sum_name': 1, }
        }

    # 模具
    def open_mold(self):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_mold_form')[1]
        mold = self.env['tokiku.mold'].sudo().search([('project_id', '=', self.env.user.project_id.id)])
        if not mold:
            mold = self.env['tokiku.mold'].sudo().create(
                {'project_id': self.env.user.project_id.id, 'name': _('Mold Demands')})
        return {
            'name': _('Mold List'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.mold',
            'res_id': mold.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_project_id': self.env.user.project_id.id}
        }

    # 需求單 (鋁擠型毛料、安裝)
    @api.multi
    def open_demand(self):
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)
        if categ:
            si = project_id.supplier_info_ids.filtered(lambda x: categ_id in [c.id for c in x.prod_catg])
        else:
            si = project_id.supplier_info_ids

        partner_ids = [s.supplier_id.id for s in si]

        tree_name = 'view_demand_tree'
        form_name = 'view_demand_form'
        res_model = 'tokiku.demand'
        if self.categ_id.code in ['raw']:
            tree_name = 'view_demand_%s_tree' % self.categ_id.code
            form_name = 'view_demand_%s_form' % self.categ_id.code
        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', tree_name)[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', form_name)[1]
        domain = [('contract_id.project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]
        if self.categ_id.code in ['mold']:
            domain = [('project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]

        return {
            'name': _('Demand List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': res_model,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {'default_project_id': self.project_id.id,
                        'default_categ_id': self.categ_id.id,
                        'default_contract_id': self.env.user.contract_id.id,
                        'supplier_ids': partner_ids}
        }

    @api.multi
    def open_installation_demand(self):
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)
        if categ:
            si = project_id.supplier_info_ids.filtered(lambda x: categ_id in [c.id for c in x.prod_catg])
        else:
            si = project_id.supplier_info_ids

        partner_ids = [s.supplier_id.id for s in si]

        res_model = 'tokiku.installation_demand'

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_demand_installation_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_demand_installation_form')[1]
        domain = [('contract_id.project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]
        # domain = [('project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]

        return {
            'name': _('Installation Demand List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': res_model,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {'default_project_id': self.project_id.id,
                        'default_categ_id': self.categ_id.id,
                        'default_contract_id': self.env.user.contract_id.id,
                        'supplier_ids': partner_ids}
        }

    # @api.multi
    # def open_valuation(self):
    #     project_id = self.env.user.project_id or self.project_id
    #     categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
    #     categ = self.env['product.category'].browse(categ_id)
    #     if categ:
    #         si = project_id.supplier_info_ids.filtered(lambda x: categ_id in [c.id for c in x.prod_catg])
    #     else:
    #         si = project_id.supplier_info_ids
    #
    #     partner_ids = [s.supplier_id.id for s in si]
    #
    #     res_model = 'tokiku.demand'
    #
    #     tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_demand_installation_tree')[1]
    #     form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_demand_installation_form')[1]
    #     domain = [('contract_id.project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]
    #     # domain = [('project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]
    #
    #     return {
    #         'name': _('Valuation'),
    #         'view_type': 'form',
    #         'view_mode': 'tree',
    #         'res_model': res_model,
    #         'views': [(tree_id, 'tree'), (form_id, 'form')],
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'domain': domain,
    #         'context': {'default_project_id': self.project_id.id,
    #                     'default_categ_id': self.categ_id.id,
    #                     'default_contract_id': self.env.user.contract_id.id,
    #                     'supplier_ids': partner_ids}
    #     }

    @api.multi
    def open_aluminum_tree_panel(self):
        return self.open_tree_panel('raw', 'Aluminum Raw Material')

    # 鋁擠型加工 新管控表
    @api.multi
    def open_refine_tree_panel(self):
        return self.open_tree_panel('aluminum', 'Aluminum Refine')

    @api.multi
    def open_glass_tree_panel(self):
        return self.open_tree_panel('glass', 'Glass')

    @api.multi
    def open_plate_tree_panel(self):
        return self.open_tree_panel('plate', 'Aluminum Plate')

    @api.multi
    def open_steel_tree_panel(self):
        return self.open_tree_panel('steel', 'Stainless Steel')

    @api.multi
    def open_iron_tree_panel(self):
        return self.open_tree_panel('iron', 'Iron Pieces')

    @api.multi
    def open_stone_tree_panel(self):
        return self.open_tree_panel('stone', 'Stone')

    @api.multi
    def open_silicon_tree_panel(self):
        return self.open_tree_panel('silicon', 'Silicon')

    @api.multi
    def open_rubber_tree_panel(self):
        return self.open_tree_panel('rubber', 'Rubber')

    @api.multi
    def open_mineral_tree_panel(self):
        return self.open_tree_panel('mineral', 'Mineral')

    @api.multi
    def open_accessories_tree_panel(self):
        return self.open_tree_panel('accessories', 'Accessories')

    @api.multi
    def open_others_tree_panel(self):
        return self.open_tree_panel('others', 'Others')

    def open_tree_panel(self, code, category_name):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        form_id = 'view_panel_line_tree'
        if code == 'raw':
            form_id = 'view_panel_line_raw_tree'

        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])
        # panel.refresh = True
        # if panel.refresh:
        #     panel.calculate()
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': _('Panel'),
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'tokiku.panel_line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_stage': 'material'},
            'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
                       ('panel_id.categ_code', '=', code)
                       ],
            'limit': 200,
        }

    def open_account_panel(self, code, category_name):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        form_id = 'view_panel_account_tree'
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])
        # panel.refresh = True
        # if panel.refresh:
        #     panel.calculate()
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': _('Panel'),
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'tokiku.panel_line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_stage': 'material'},
            'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
                       ('panel_id.categ_code', '=', code)
                       ],
            'limit': 200,
        }

    @api.multi
    def open_refine_account_panel(self):
        return self.open_account_panel('aluminum', 'Aluminum Refine')

    @api.multi
    def open_plate_account_panel(self):
        return self.open_account_panel('plate', 'Aluminum Plate')

    @api.multi
    def open_steel_account_panel(self):
        return self.open_account_panel('steel', 'Stainless Steel')

    @api.multi
    def open_iron_account_panel(self):
        return self.open_account_panel('iron', 'Iron Pieces')

    @api.multi
    def open_others_account_panel(self):
        return self.open_account_panel('others', 'Others')

    @api.multi
    def open_aluminum_panel(self):
        return self.open_panel('raw', 'Aluminum Raw Material')

    @api.multi
    def open_refine_panel(self):
        return self.open_panel('aluminum', 'Aluminum Refine')

    @api.multi
    def open_glass_panel(self):
        return self.open_panel('glass', 'Glass')

    @api.multi
    def open_plate_panel(self):
        return self.open_panel('plate', 'Aluminum Plate')

    @api.multi
    def open_steel_panel(self):
        return self.open_panel('steel', 'Stainless Steel')

    @api.multi
    def open_iron_panel(self):
        return self.open_panel('iron', 'Iron Pieces')

    @api.multi
    def open_stone_panel(self):
        return self.open_panel('stone', 'Stone')

    @api.multi
    def open_silicon_panel(self):
        return self.open_panel('silicon', 'Silicon')

    @api.multi
    def open_rubber_panel(self):
        return self.open_panel('rubber', 'Rubber')

    @api.multi
    def open_mineral_panel(self):
        return self.open_panel('mineral', 'Mineral')

    @api.multi
    def open_accessories_panel(self):
        return self.open_panel('accessories', 'Accessories')

    @api.multi
    def open_others_panel(self):
        return self.open_panel('others', 'Others')

    # @api.multi
    # def open_installation_panel(self):
    #     return self.open_panel('installation', 'Installation')

    # 管控表 (鋁擠型毛料、鋁擠型加工、材料)
    def open_panel(self, code, category_name):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        form_id = 'view_panel_form'
        if code in ['raw']:
            form_id = 'view_panel_%s_form' % code

        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])

        # panel.refresh = True
        if code in ['raw', 'mold']:
            panel.refresh = True

        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': panel.categ_id.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.panel',
            'res_id': panel.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_categ_id': categ.id,
                        'default_contract_id': self.id,
                        'categ_code': categ.code}
        }

    # 組裝管控表
    @api.multi
    def open_assembly_panel(self):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        code = 'assembly'
        category_name = 'Assembly'
        form_id = 'view_panel_assembly_tree'

        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': _('Assembly Panel'),
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'tokiku.assembly_panel_line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_stage': 'material'},
            'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
                       ('panel_id.categ_code', '=', code)]
        }

    # 備料管控表 (組裝)
    @api.multi
    def open_assembly_preparation_panel(self):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        code = 'assembly'
        category_name = 'Assembly'
        form_id = 'view_panel_assembly_preparation_tree'

        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': _('Preparation Panel'),
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'tokiku.assembly_panel_line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_stage': 'material'},
            'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
                       ('panel_id.categ_code', '=', code)]
        }

    # 組裝總表
    @api.multi
    def open_summary_panel(self):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        code = 'assembly'
        category_name = 'Assembly'
        form_id = 'view_panel_summary_tree'

        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': _('Assembly Summary'),
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'tokiku.assembly_panel_line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_stage': 'material'},
            'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
                       ('panel_id.categ_code', '=', code)]
        }

    # 安裝管控表
    @api.multi
    def open_installation_panel(self):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        code = 'installation'
        category_name = 'Installation'
        form_id = 'view_panel_installation_tree'

        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': _('Installation Panel'),
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'tokiku.installation_panel_line',
            'res_id': panel.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_stage': 'installation',
                        'default_categ_id': categ.id,
                        'default_contract_id': self.id,
                        }
            # 'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
            #            ('panel_id.categ_code', '=', code)]
        }

    # # 安裝總表
    # @api.multi
    # def open_installation_summary_panel(self):
    #     if not self.env.user.project_id:
    #         raise UserError(_('Please select a project first!'))
    #         return
    #
    #     code = 'installation'
    #     category_name = 'Installation'
    #     form_id = 'view_installation_summary_tree'
    #
    #     view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
    #     categ = self.env['product.category'].sudo().search([('code', '=', code)])
    #     if not categ:
    #         categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
    #     panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
    #                                                     ('categ_id', '=', categ.id)])
    #     if not panel:
    #         panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
    #                                                         'categ_id': categ.id})
    #     return {
    #         'name': _('Installation Summary'),
    #         # 'view_type': 'tree',
    #         'view_mode': 'tree',
    #         'res_model': 'tokiku.installation_panel_line',
    #         'type': 'ir.actions.act_window',
    #         'view_id': view_id,
    #         'target': 'current',
    #         'flags': {'form': {'action_buttons': True}},
    #         'context': {'default_stage': 'installation'},
    #         # 'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
    #         #            ('panel_id.categ_code', '=', code)]
    #     }

    # # 工地安裝進度表
    # @api.multi
    # def open_installation_progress_panel(self):
    #     if not self.env.user.project_id:
    #         raise UserError(_('Please select a project first!'))
    #         return
    #
    #     code = 'installation'
    #     category_name = 'Installation'
    #     form_id = 'view_installation_progress_tree'
    #
    #     view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
    #     categ = self.env['product.category'].sudo().search([('code', '=', code)])
    #     if not categ:
    #         categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
    #     panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
    #                                                     ('categ_id', '=', categ.id)])
    #     if not panel:
    #         panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
    #                                                         'categ_id': categ.id})
    #     return {
    #         'name': _('Installation Progress'),
    #         'view_mode': 'tree',
    #         'res_model': 'tokiku.installation_panel_line',
    #         'type': 'ir.actions.act_window',
    #         'view_id': view_id,
    #         'target': 'current',
    #         'flags': {'form': {'action_buttons': True}},
    #         'context': {'default_stage': 'material'},
    #         # 'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
    #         #            ('panel_id.categ_code', '=', code)]
    #     }

    # 訂製單 (模具、鋁擠型毛料、鋁擠型加工、輔助材料)
    @api.multi
    def open_po(self):
        tree_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_tree')[1]
        contract_id = self.env.user.contract_id
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)  # EX: categ.code output aluminum.
        stage = self.env.context.get('default_stage')

        po_category = self.env['tokiku.order_category'].search([('code', '=', 'normal')], limit=1)
        if categ:
            si = project_id.supplier_info_ids.filtered(lambda x: categ_id in [c.panel_categ_id.id for c in x.prod_catg])

        else:
            si = project_id.supplier_info_ids

        partner_ids = [s.supplier_id.id for s in si]
        ctx = {
            'supplier_ids': partner_ids,
            'default_categ_id': categ_id,
            'default_project_id': project_id.id,
            'default_contract_id': contract_id.id,
            'default_panel_id': self.id,
            'default_stage': stage,
            'default_date_planned': fields.Date.today(),
            'show_demand': True,
            'show_spare': True,
            'panel_id': self.id,
            'default_po_category_id': po_category.id,
            'contract_ids': [c.id for c in project_id.contract_ids],
        }
        domain = [('project_id', '=', project_id.id), ('categ_id', '=', categ_id), ('stage', '=', 'material')]
        if categ.code == 'mold':
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_mold_order_form')[1]
        elif categ.code == 'raw':
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_raw_order_form')[1]
        elif categ.code == 'aluminum':
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_refine_order_form')[1]
        else:
            form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_other_order_form')[1]

        return {
            'name': _('Order Form'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': ctx,
            'default_panel_id': self.id,
        }

    # 組裝訂製單
    @api.multi
    def open_assembly_po(self):
        tree_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_tree')[1]
        contract_id = self.env.user.contract_id
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)  # EX: categ.code output aluminum.
        stage = self.env.context.get('default_stage')

        po_category = self.env['tokiku.order_category'].search([('code', '=', 'normal')], limit=1)
        if categ:
            si = project_id.supplier_info_ids.filtered(lambda x: categ_id in [c.panel_categ_id.id for c in x.prod_catg])

        else:
            si = project_id.supplier_info_ids

        partner_ids = [s.supplier_id.id for s in si]
        ctx = {
            'supplier_ids': partner_ids,
            'default_categ_id': categ_id,
            'default_project_id': project_id.id,
            'default_contract_id': contract_id.id,
            'default_panel_id': self.id,
            'default_factory_id': partner_ids[0] if len(partner_ids) > 0 else None,
            'default_partner_id': partner_ids[0] if len(partner_ids) > 0 else None,
            'default_stage': stage,
            'default_date_planned': fields.Date.today(),
            'show_demand': True,
            'show_spare': True,
            'display_default_code': False,
            'panel_id': self.id,
            'default_po_category_id': po_category.id,
            'contract_ids': [c.id for c in project_id.contract_ids],
        }
        domain = [('project_id', '=', project_id.id), ('categ_id', '=', categ_id), ('stage', '=', 'assembly')]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_assembly_purchase_order_form')[1]

        return {
            'name': _('Assembly Order Form'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': ctx,
            'default_panel_id': self.id,
        }

    # 安裝訂製單
    @api.multi
    def open_installation_po(self):
        tree_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_tree')[1]
        contract_id = self.env.user.contract_id
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)  # EX: categ.code output aluminum.
        stage = self.env.context.get('default_stage')
        po_category = self.env['tokiku.order_category'].search([('code', '=', 'normal')], limit=1)
        if categ:
            si = project_id.supplier_info_ids.filtered(lambda x: categ_id in [c.panel_categ_id.id for c in x.prod_catg])

        else:
            si = project_id.supplier_info_ids

        partner_ids = [s.supplier_id.id for s in si]
        ctx = {
            'supplier_ids': partner_ids,
            'default_categ_id': categ_id,
            'default_project_id': project_id.id,
            'default_contract_id': contract_id.id,
            'default_panel_id': self.id,
            'default_factory_id': partner_ids[0] if len(partner_ids) > 0 else None,
            'default_partner_id': partner_ids[0] if len(partner_ids) > 0 else None,
            'default_stage': stage,
            'default_date_planned': fields.Date.today(),
            'show_demand': True,
            'show_spare': True,
            'display_default_code': False,
            'panel_id': self.id,
            'default_po_category_id': po_category.id,
            'contract_ids': [c.id for c in project_id.contract_ids],
        }
        domain = [('project_id', '=', project_id.id), ('categ_id', '=', categ_id), ('stage', '=', 'installation')]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_installation_order_form')[1]

        return {
            'name': _('Installation Order Form'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': ctx,
            'default_panel_id': self.id,
        }

    # 備料派工單
    @api.multi
    def open_preparation_order(self):
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)
        # if categ:
        #     si = project_id.supplier_info_ids.filtered (lambda x: categ_id in [c.id for c in x.prod_catg])
        # else:
        #     si = project_id.supplier_info_ids
        # partner_ids = [s.supplier_id.id for s in si]

        tree_name = 'view_preparation_order_tree'
        form_name = 'view_preparation_order_form'
        res_model = 'tokiku.preparation_order'

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', tree_name)[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', form_name)[1]
        partner_ids = [l.supplier_id.id for l in self.assembly_panel_line_ids]
        factory_ids = [s.id for s in
                       self.project_id.supplier_info_ids.filtered(lambda x: x.prod_catg.code == 'assembly')]
        domain = [('contract_id.project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]
        # if self.categ_id.code in ['mold']:
        #     domain = [('project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]

        return {
            'name': _('Preparation Order List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': res_model,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {'default_project_id': self.project_id.id,
                        'default_categ_id': self.categ_id.id,
                        'default_contract_id': self.env.user.contract_id.id,
                        'default_factory_id': partner_ids[0] if len(partner_ids) > 0 else None,
                        'default_partner_id': partner_ids[0] if len(partner_ids) > 0 else None,
                        'panel_id': self.id,
                        'partner_ids': partner_ids,
                        'factory_ids': factory_ids,
                        }
        }

    # 組裝派工單
    @api.multi
    def open_assembly_order(self):
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)

        tree_name = 'view_assembly_order_tree'
        form_name = 'view_assembly_order_form'
        res_model = 'tokiku.assembly_order'

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', tree_name)[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', form_name)[1]
        partner_ids = [l.supplier_id.id for l in self.assembly_panel_line_ids]
        factory_ids = [s.id for s in
                       self.project_id.supplier_info_ids.filtered(lambda x: x.prod_catg.code == 'assembly')]
        domain = [('contract_id.project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]

        return {
            'name': _('Assembly Order List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': res_model,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {'default_project_id': self.project_id.id,
                        'default_categ_id': self.categ_id.id,
                        'default_contract_id': self.env.user.contract_id.id,
                        'default_factory_id': partner_ids[0] if len(partner_ids) > 0 else None,
                        'default_partner_id': partner_ids[0] if len(partner_ids) > 0 else None,
                        'default_date_planned': fields.Date.today(),
                        'panel_id': self.id,
                        'partner_ids': partner_ids,
                        'factory_ids': factory_ids,
                        },
        }

    # 組裝生產紀錄單
    @api.multi
    def open_production_record(self):
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)

        tree_name = 'view_production_record_order_tree'
        form_name = 'view_production_record_order_form'
        res_model = 'tokiku.production_record'

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', tree_name)[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', form_name)[1]
        partner_ids = [l.supplier_id.id for l in self.assembly_panel_line_ids]
        factory_ids = [s.id for s in
                       self.project_id.supplier_info_ids.filtered(lambda x: x.prod_catg.code == 'assembly')]
        domain = [('contract_id.project_id', '=', self.project_id.id), ('categ_id', '=', self.categ_id.id)]

        return {
            'name': _('Production Record Order List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': res_model,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {'default_project_id': self.project_id.id,
                        'default_categ_id': self.categ_id.id,
                        'default_contract_id': self.env.user.contract_id.id,
                        'default_factory_id': partner_ids[0] if len(partner_ids) > 0 else None,
                        'default_supplier_info_id': partner_ids[0] if len(partner_ids) > 0 else None,
                        'panel_id': self.id,
                        'partner_ids': partner_ids,
                        'factory_ids': factory_ids,
                        },
        }

    # 安裝生產紀錄單
    @api.multi
    def open_installation_production_record(self):
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)

        tree_name = 'view_installation_production_record_order_tree'
        form_name = 'view_installation_production_record_order_form'
        res_model = 'tokiku.inst_prodrec'

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', tree_name)[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', form_name)[1]
        location_dest_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('location_id.name', '=', 'Installation'),
             ('name', '=', 'Done')])
        location_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('location_id.name', '=', 'Installation'),
             ('name', '=', 'Pending')])
        src_location_ids = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'), ('location_id.name', '=', 'Installation')])
        location_ids = [x.id for x in src_location_ids]
        domain = [('contract_id.project_id', '=', self.project_id.id),
                  ('categ_id', '=', self.categ_id.id),
                  ]

        return {
            'name': _('Production Record Order List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': res_model,
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {'default_project_id': self.project_id.id,
                        'default_categ_id': self.categ_id.id,
                        'default_contract_id': self.env.user.contract_id.id,
                        'default_location_id': location_id.id,
                        'default_location_dest_id': location_dest_id.id,
                        'panel_id': self.id,
                        'location_ids': location_ids
                        },
        }

    # 鋁擠型加工 加工訂製單
    @api.multi
    def open_process_po(self):
        tree_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_tree')[1]
        contract_id = self.env.user.contract_id or self.contract_id
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)
        stage = self.env.context.get('default_stage')
        stage_categ = self.env['product.category'].search([('code', '=', stage)])

        if stage_categ:
            si = project_id.supplier_info_ids.filtered(lambda x: stage_categ.id in [c.id for c in x.prod_catg])
        else:
            si = project_id.supplier_info_ids
        partner_ids = [s.supplier_id.id for s in si]

        domain = [('project_id', '=', project_id.id),
                  ('categ_id', '=', categ_id),
                  ('stage', '=', stage), ]
        ctx = {'supplier_ids': partner_ids,  # [s.supplier_id.id for s in ]
               'default_categ_id': categ_id,
               'default_project_id': project_id.id,
               'default_contract_id': contract_id.id,
               'default_date_planned': fields.Date.today(),
               'show_demand': True,
               'default_panel_id': self.id,
               'default_stage': stage,
               'contract_ids': [c.id for c in project_id.contract_ids],
               }

        if stage and stage != 'material':
            if categ.code == 'aluminum':
                form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_process_order_form')[1]
            else:
                # 鋁擠型外材料訂製單 / 鋁擠型外加工訂製單 / 鋁擠型外烤漆訂製單
                form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_other_order_form')[1]

        return {
            'name': '%s%s' % (stage_categ.name, _('Order Form')),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': ctx,
            'default_panel_id': self.id,
        }

    # 已安裝進料單
    @api.multi
    def open_installation_valuation(self):
        tree_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_tree')[1]
        contract_id = self.env.user.contract_id or self.contract_id
        project_id = self.env.user.project_id or self.project_id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)
        stage = self.env.context.get('default_stage')
        stage_categ = self.env['product.category'].search([('code', '=', stage)])

        if stage_categ:
            si = project_id.supplier_info_ids.filtered(lambda x: stage_categ.id in [c.id for c in x.prod_catg])
        else:
            si = project_id.supplier_info_ids
        partner_ids = [s.supplier_id.id for s in si]

        domain = [('project_id', '=', project_id.id),
                  ('categ_id', '=', categ_id),
                  ('stage', '=', stage), ]
        ctx = {'supplier_ids': partner_ids,  # [s.supplier_id.id for s in ]
               'default_categ_id': categ_id,
               'default_project_id': project_id.id,
               'default_contract_id': contract_id.id,
               'default_date_planned': fields.Date.today(),
               'show_demand': True,
               'default_panel_id': self.id,
               'default_stage': stage,
               'contract_ids': [c.id for c in project_id.contract_ids],
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_installation_valuation_form')[1]

        return {
            'name': _('Installation Valuation'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': ctx,
            'default_panel_id': self.id,
        }

    @api.multi
    def open_order_panel(self):
        view_id = self.env['ir.model.data'].sudo().get_object_reference('tokiku', 'view_order_panel_form')[1]
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)

        return {
            'name': _('Order Panel'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.panel',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_project_id': self.project_id.id, 'default_categ_id': categ.id,
                        'default_categ_code': categ.code, 'panel_type': 'order',
                        'default_panel_id': self.id, }
        }

    @api.multi
    def open_receive(self):
        tree_id = self.env['ir.model.data'].get_object_reference('stock_picking_wave', 'view_picking_wave_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('stock_picking_wave', 'view_picking_wave_form')[1]

        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        picking_type = self.env['stock.picking.type'].search(
            [('warehouse_id', '=', warehouse_id.id), ('code', '=', 'incoming')], limit=1)
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)
        if categ.code == 'mold':
            domain = [('project_id', '=', self.project_id.id), ('picking_ids.picking_type_id', '=', picking_type.id)]
            ctx = {'default_categ_id': self.categ_id.id, 'default_project_id': self.project_id.id,
                   'default_picking_type_id': picking_type.id}
        else:
            domain = [('contract_id', '=', self.env.user.contract_id.id), ('categ_id', '=', self.categ_id.id),
                      ('picking_ids.picking_type_id', '=', picking_type.id)]
            ctx = {'default_categ_id': self.categ_id.id, 'default_contract_id': self.env.user.contract_id.id,
                   'default_picking_type_id': picking_type.id}
        return {
            'name': _('Receive Return'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.picking.wave',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': ctx
        }

    @api.multi
    def open_picking(self):
        project_id = self.env.user.project_id.id or self.project_id.id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        categ = self.env['product.category'].browse(categ_id)
        form_name = _('Picking')
        if categ.code == 'mold':
            picking_type = self.env['stock.picking.type'].with_context(lang=None).search(
                [('code', '=', 'internal'), ('name', '=', 'Internal Transfers')], limit=1)
            domain = [('project_id', '=', self.project_id.id),
                      ('picking_type_id', '=', picking_type.id)]
            ctx = {'contact_display': 'partner_address',
                   'default_categ_id': self.categ_id.id,
                   'default_project_id': self.project_id.id,
                   'default_picking_type_id': picking_type.id}
        else:
            stage = self.env.context.get('default_stage')
            picking_type = self.env['stock.picking.type'].with_context(lang=None).search(
                [('code', '=', 'internal'), ('name', '=', 'Internal Transfers')], limit=1)

            if stage in ['ship', 'refine', 'heat', 'paint', 'assembly', 'site']:
                location_name = stage.capitalize()
                if stage == 'ship':
                    form_name = _('Ship')
                elif stage == 'refine':
                    form_name = _('Refine')
                elif stage == 'heat':
                    form_name = _('Heat')
                elif stage == 'paint':
                    form_name = _('Paint')
                elif stage == 'assembly':
                    form_name = _('Assembly')
                elif stage == 'site':
                    form_name = _('Site')

                stages = ['Ship', 'Refine', 'Heat', 'Paint', 'Assembly', 'Site', '']
                if categ.code == 'glass':
                    stages = ['Ship', 'Refine', 'Assembly', 'Site', '']
                # elif categ.code != 'aluminum':
                #     stages = ['Ship', 'Refine', 'Paint', 'Assembly', 'Site', '']
                location_done_id = self.env['stock.location'].with_context(lang=None).search(
                    [('usage', '=', 'internal'), ('location_id.name', '=', location_name),
                     ('name', '=', 'Done')], limit=1)

                location_next_name = stages[stages.index(location_name) + 1]
                location_next_id = self.env['stock.location'].with_context(lang=None).search(
                    [('usage', '=', 'internal'), ('location_id.name', '=', location_next_name),
                     ('name', '=', 'Pending')], limit=1)
                location_site_id = self.env['stock.location'].with_context(lang=None).search(
                    [('usage', '=', 'internal'), ('name', '=', 'Site')])
                if stage == 'ship':
                    src_location_ids = self.env['stock.location'].with_context(lang=None).search(
                        [('usage', '=', 'internal'), ('name', '=', 'Stock')], limit=1)
                    location_id = self.env['stock.location'].with_context(lang=None).search(
                        [('usage', '=', 'internal'), ('name', '=', 'Stock')])
                    location_dest_id = location_next_id
                else:
                    src_location_ids = self.env['stock.location'].with_context(lang=None).search(
                        [('usage', '=', 'internal'), ('location_id.name', '=', location_name)])
                    location_id = self.env['stock.location'].with_context(lang=None).search(
                        [('usage', '=', 'internal'), ('location_id.name', '=', location_name),
                         ('name', '=', 'Pending')], limit=1)
                    location_dest_id = location_done_id

                location_ids = [x.id for x in src_location_ids]

                sup_location_ids = self.env['stock.location'].with_context(lang=None).search(
                    [('usage', '=', 'internal'), '|', ('location_id.name', '=', location_name), '&',
                     ('location_id.name', 'in', stages),
                     ('name', 'in', ['Pending'])])
                location_dest_ids = [x.id for x in sup_location_ids]

                # quants = self.env['stock.quant'].search(
                #     [('location_id', '=', location_id.id),  # ('partner_id', '!=', False),
                #      ('product_id.project_id', '=', project_id),
                #      ('product_id.categ_id.panel_categ_id', '=', categ_id)
                #      ])
                # mls = []
                # partner_ids = []
                # qtys = {}
                # product_ids = {}
                # src_partner_ids = {}
                # panel_ids = {}
                # for q in quants:
                #     print q.id
                #     if q.partner_id.id not in partner_ids:
                #         partner_ids.append(q.partner_id.id)
                #
                #     group_key = "%s/%s" % (q.product_id.id, q.history_ids[0].atlas_id.id)
                #     if group_key in qtys:
                #         qtys[group_key] += q.qty
                #
                #     else:
                #         qtys[group_key] = q.qty
                #         panel_ids[group_key] = q.history_ids[0].panel_line_id
                #         product_ids[group_key] = q.product_id
                #         src_partner_ids[group_key] = q.partner_id.id
                #
                #     location_name = location_dest_id.location_id.with_context(lang=None).name
                #     for k in qtys:
                #         print k
                #         if qtys[k] > 0:
                #             tmp_coating = panel_ids[k].surface_coating or ''
                #             tmp_heating = panel_ids[k].heating or ''
                #
                #             if location_name in ['Refine', 'Assembly'] or (
                #                     location_name == 'Heat' and len(parse_str(tmp_heating).replace("'", "")) > 0) or (
                #                     location_name == 'Paint' and len(parse_str(tmp_coating).replace("'", "")) > 0):
                #                 mls.append({
                #                     'name': product_ids[k].name,
                #                     'panel_line_id': panel_ids[k].id,
                #                     # 'date': datetime.now(),
                #                     'company_id': self.env['res.company']._company_default_get('stock.move'),
                #                     'date_expected': datetime.now(),
                #                     'product_id': product_ids[k].id,
                #                     'product_uom': product_ids[k].uom_id.id,
                #                     'product_uom_qty': qtys[k],
                #                     'location_id': location_id.id,
                #                     'location_dest_id': location_dest_id.id,
                #                     # 'owner_id': self.partner_id.id,
                #                     'procure_method': 'make_to_stock',
                #                     'state': 'draft',
                #                 })
                ctx = {'stage': stage, 'contact_display': 'partner_address', 'default_categ_id': self.categ_id.id,
                       'default_contract_id': self.env.user.contract_id.id, 'default_location_id': location_id.id,
                       'default_location_dest_id': location_dest_id.id, 'default_picking_type_id': picking_type.id,
                       'location_ids': location_ids, 'stages': stages, 'location_dest_ids': location_dest_ids,
                       'location_done_id': location_done_id.id, 'location_next_id': location_next_id.id,
                       'location_site_id': location_site_id.id}
                # , 'default_move_lines': mls,
            else:
                ctx = {'default_contract_id': self.env.user.contract_id.id, 'stage': 'material'}
            domain = [('project_id', '=', self.env.user.project_id.id), ('categ_id', '=', self.categ_id.id), (
                'stage', '=', stage)]

        return {
            'name': form_name,
            'view_type': 'form',
            'view_mode': 'tree,kanban,form,calendar',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': ctx
        }

    def as_po_dict(self, supplier_id, atlas_ids):
        stage = self.env.context.get('default_stage')
        contract_id = self.env.context.get('default_contract_id')
        project_id = self.env.user.project_id.id or self.project_id.id
        supplier_id = supplier_id or self.env.context.get('default_supplier_id')
        po_dict = []

        if stage and stage != 'material':
            categ_id = self.env.context.get('default_categ_id') or self.categ_id.id

            if stage in ['ship', 'refine', 'heat', 'paint', 'assembly']:
                location_name = stage.capitalize()

            domain = [('location_id.name', '=', 'Pending'),  # ('partner_id', '!=', False),
                      ('location_id.location_id.name', '=', location_name),
                      ('product_id.project_id', '=', project_id),
                      ('product_id.categ_id.panel_categ_id', '=', categ_id),
                      # ('rest_demand_qty', '>', 0),
                      ]
            if len(atlas_ids) > 0:
                domain.append(('panel_line_id.atlas_id', 'in', [a.id for a in atlas_ids]))

            quants = self.env['stock.quant'].with_context(lang=None).search(domain)

            refine_order_qty = {}  # obtain quants qty to order line
            for q in quants:
                p_line_id = q.panel_line_id.id
                for h in q.history_ids:
                    if h.product_qty > 0:
                        if refine_order_qty.get(p_line_id):
                            refine_order_qty[p_line_id] += h.product_qty
                        else:
                            refine_order_qty[p_line_id] = h.product_qty

            lines = [q.panel_line_id for q in quants]

        # elif self.categ_code == 'aluminum' and stage == 'material':
        #     raw_order = self.env['purchase.order'].search([('categ_code', '=', 'raw'),
        #                                                    ('state', '=', 'purchase'),
        #                                                    # ('partner_id', '=', supplier_id),
        #                                                    ('contract_id', '=', contract_id)
        #                                                    ])
        #     mold_num = []
        #     for o in raw_order:
        #         for l in o.order_line:
        #             if l.default_code not in mold_num:
        #                 mold_num.append(l.default_code)
        #
        #     lines = self.line_ids.filtered(lambda x: x.rest_demand_qty > 0 and x.code in mold_num)

        elif self.categ_code == 'raw' and stage == 'material':
            mold_order = self.env['purchase.order'].search([('categ_code', '=', 'mold'),
                                                            ('state', 'in', ['purchase', 'done']),
                                                            ('partner_id', '=', supplier_id),
                                                            ('contract_id', '=', contract_id)
                                                            ])
            mold_num = []
            for o in mold_order:
                for l in o.order_line:
                    if l.default_code not in mold_num:
                        mold_num.append(l.default_code)

            lines = self.line_ids.filtered(lambda x: x.rest_demand_qty > 0 and x.default_code in mold_num)

        elif len(atlas_ids) > 0:
            lines = self.line_ids.filtered(
                lambda x: x.rest_demand_qty > 0 and x.default_code and x.atlas_id.id in [a.id for a in atlas_ids])
            # lines = self.env['tokiku.panel_line'].search([('panel_id', '=', self.id),
            #                                               ('rest_demand_qty', '>', 0),
            #                                               ('atlas_id', 'in', [a.id for a in atlas_ids])
            #                                               ])
        else:
            lines = self.line_ids.filtered(lambda x: x.rest_demand_qty > 0 and x.default_code)

        for line in lines:
            product_id = line.product_id.id
            default_code = line.product_id.default_code
            order_length = line.cutting_length
            order_width = line.cutting_width
            order_qty = line.rest_demand_qty
            refine_weight = 0
            if stage and stage != 'material':
                process_fee = self.env['product.product'].search([('default_code', '=', '%s_fee' % stage),
                                                                  ('type', '=', 'service')], limit=1)
                product_id = process_fee.id
                material = line.material
                default_code = line.default_code
                refine_weight = line.weight

                if stage == 'refine':
                    service_order_qty = refine_order_qty[line.id] - line.refine_order_qty
                elif stage == 'heat':
                    service_order_qty = refine_order_qty[line.id] - line.heat_order_qty
                elif stage == 'paint':
                    service_order_qty = refine_order_qty[line.id] - line.paint_order_qty
                order_qty = service_order_qty

            elif self.categ_code == 'mold':
                material = line.mold_material
                order_length = line.product_id.volume
                order_width = line.product_id.order_width
            elif self.categ_code == 'raw' or 'aluminum':
                material = line.material  # 2018/12/11
            if self.categ_code not in ['mold'] or line.seller_id.name.id == supplier_id:
                po_dict.append({
                    'name': line.product_id.name,
                    'atlas_id': line.atlas_id.id,
                    'product_id': product_id,
                    'product_uom': line.product_id.uom_po_id.id,
                    'demand_qty': line.demand_qty,
                    'rest_demand_qty': line.rest_demand_qty,
                    'spare_qty': 0,
                    'order_qty': order_qty,
                    'total_ordered_qty': line.order_qty + line.qty_backorder,
                    'order_length': order_length,
                    'order_width': order_width,
                    'code': line.code,
                    'color_code': line.color_code,
                    'surface_coating': line.surface_coating,
                    'description': line.description,
                    'pricing_area': '',
                    'estimated_delivery_date': '',
                    'default_code': default_code,
                    'material': material,
                    'prod_categ_id': line.prod_categ_id.id,
                    'seller_id': line.seller_id.id,
                    'refine_weight': refine_weight,
                    'mold_id': line.mold_id.id,
                    'mold_seller_id': line.mold_seller_id.id,
                    'panel_line_id': line.id,
                    'panel_id': line.panel_id.id,
                })
            else:
                if line.seller_id.name.id == supplier_id:
                    po_dict.append({
                        'name': line.product_id.name,
                        'atlas_id': line.atlas_id.id,
                        'product_id': product_id,
                        'product_uom': line.product_id.uom_po_id.id,
                        'demand_qty': line.demand_qty,
                        'rest_demand_qty': line.rest_demand_qty,
                        'spare_qty': 0,
                        'order_qty': order_qty,
                        'total_ordered_qty': line.order_qty + line.qty_backorder,
                        'order_length': order_length,
                        'order_width': order_width,
                        'code': line.code,
                        'color_code': line.color_code,
                        'surface_coating': line.surface_coating,
                        'description': line.description,
                        'pricing_area': '',
                        'estimated_delivery_date': '',
                        'default_code': default_code,
                        'material': material,
                        'prod_categ_id': line.prod_categ_id.id,
                        'seller_id': line.seller_id.id,
                        'refine_weight': refine_weight,
                        'mold_id': line.mold_id.id,
                        'mold_seller_id': line.mold_seller_id.id,
                        'panel_line_id': line.id,
                        'panel_id': line.panel_id.id,
                    })

        return po_dict

    def install_po_dict(self, supplier_id):
        stage = self.env.context.get('default_stage')
        supplier_id = supplier_id or self.env.context.get('default_supplier_id')
        po_dict = []

        lines = self.installation_panel_line_ids.filtered(lambda x: x.rest_demand_qty > 0)

        for line in lines:
            product_id = line.product_id.id

            if self.categ_code in ['installation'] or line.seller_id.name.id == supplier_id:
                po_dict.append({
                    'product_id': product_id,
                    'product_uom': line.product_id.uom_po_id.id,
                    'name': line.product_id.name,
                    'atlas_name': line.atlas_name,
                    'building_id': line.building_id.id,
                    'install_categ': line.install_categ_id.id,
                    'product_categ': line.product_categ,
                    'install_loc': line.install_loc_id.id,
                    'demand_qty': line.demand_qty,
                    'default_code': line.default_code,
                    'floor': line.floor,
                    'rest_demand_qty': line.rest_demand_qty,
                    'order_qty': line.rest_demand_qty,
                    'install_panel_line_id': line.id,
                    'installed_qty': line.installed_qty,
                    'installed_surface': line.installed_surface,
                    'panel_id': line.panel_id.id,
                })

        return po_dict


class PanelLine(models.Model):
    _name = 'tokiku.panel_line'
    _order = 'sequence, id asc'

    name = fields.Char(string='Name', related='product_id.name')
    sequence = fields.Integer(related='atlas_id.edit_atlas_id.sequence')
    product_id = fields.Many2one('product.product', string='Product')
    default_code = fields.Char(related='product_id.default_code', store=True)
    seller_id = fields.Many2one('product.supplierinfo', string='Supplier')
    supplier_name = fields.Many2one('res.partner')  # related='product_id.supplier_name'
    seller_name = fields.Char(string='Supplier', related='seller_id.name.ref')
    supplier_part_no = fields.Char(string='Supplier Part Number')  # related='seller_id.product_code'
    description = fields.Char('Specification')
    material = fields.Char('Material')  # related='product_id.name'

    mold_supplier_part_no = fields.Char(string='Supplier Part Number', related='seller_id.product_code', store=True)
    mold_material = fields.Char(related='seller_id.product_material', store=True)
    mold_weight = fields.Float(string='Unit Weight', compute='_compute_mold_weight', store=True)

    weight = fields.Float(string='Unit Weight', compute='_compute_weight', store=True)
    volume = fields.Float(related='product_id.volume')
    length = fields.Integer(compute='_compute_length', store=True)
    paint_area = fields.Float(related='product_id.paint_area', digits=dp.get_precision('Product Unit of Measure'),
                              store=True)
    # compute = '_compute_paint_area',
    coating = fields.Float(compute='_compute_coating', store=True)
    min_qty = fields.Float(related='seller_id.min_qty')
    ingot = fields.Char(related='seller_id.ingot', store=True)
    atlas_id = fields.Many2one('tokiku.atlas', string='Processing Atlas')  # related='tokiku.atlas_line.name'
    unit_area = fields.Float('Unit Area', compute='_compute_unit_area', store=True)

    # Below details won't show at panel, these are invisible column for order form.
    cutting_length = fields.Float(string='Cutting Length')
    cutting_width = fields.Float(string='Cutting width')
    code = fields.Char(string='Code')
    mold_id = fields.Many2one('product.product',
                              compute='_compute_mold_id')  # , store=Truerelated='product_id.mold_id',
    mold_seller_id = fields.Many2one('res.partner', string='Mold Seller',
                                     compute='_compute_mold_seller_id', store=True)
    color_code = fields.Char(string='Color Code')
    heating = fields.Char(string='Heating')
    surface_coating = fields.Char(string='Surface Coating')
    atlas_unit_qty = fields.Float('Unit Quantity')
    atlas_bom = fields.Char('BOM Number')
    assembly_section = fields.Char('Assembly Section')
    # atlas_description = fields.Char(string='Atlas Description')

    mold_demand_qty = fields.Float(string='Mold Demand Quantity')
    demand_qty = fields.Integer(string='Demand Quantity')
    atlas_demand_qty = fields.Float(string='Demand Quantity in Atlas')
    weight_sub = fields.Float(string='Weight Subtotal', compute='_compute_weight_sub', store=True)

    rest_demand_qty = fields.Integer(string='Rest Demand Quantity')
    # rest_demand_qty_store = fields.Integer(string='Rest Demand Quantity', related='rest_demand_qty', store=True)
    rest_demand_weight = fields.Float(string='Rest Demand Weight', compute='_compute_weight_sub', store=True)
    xx_demand_qty = fields.Char(string='Demand Quantity Unfolded')

    # special add for panel material sum use:
    # demand_qty_rel = fields.Integer(string='Demand Quantity', related='demand_qty', store=True)
    # weight_sub_rel = fields.Float(string='Weight Subtotal', related='weight_sub', store=True)
    # rest_demand_weight_store = fields.Float(string='Rest Demand Weight', related='rest_demand_weight', store=True)

    # 材料訂單
    order_line_ids = fields.One2many('purchase.order.line', 'panel_line_id', string='Order Lines', delete='cascade')
    # ,compute='_compute_order_lines', store=True)
    order_qty = fields.Integer(string='Order Quantity') # , compute='_compute_order_qty')
    spare_qty = fields.Integer('Spare Qty')
    qty_backorder = fields.Integer(string='Quantity Backorder')  # 補料小計
    total_ordered_qty = fields.Integer('Total Ordered Qty')
    order_weight = fields.Float(string='Order Weight')  # , store=True
    # order_weight_store = fields.Float(string='Order Weight', related='order_weight', store=True)
    order_area = fields.Float(string='Order Area')
    xx_order_qty = fields.Char(string='Order Quantity Unfolded')

    qty_received = fields.Integer(string='Quantity Received')
    received_weight = fields.Float(string='Weight Received')
    out_of_stock_qty = fields.Integer(string='Out of Stock Qty')

    xx_qty_received = fields.Char(string='Quantity Received Unfolded')

    qty_returned = fields.Integer(string='Quantity Returned')
    returned_weight = fields.Float(string='Weight Returned')
    xx_qty_returned = fields.Char(string='Quantity Returned Unfolded')
    #
    qty_backed = fields.Integer(string='Quantity Backed')
    backed_weight = fields.Float(string='Weight Backed')
    xx_qty_backed = fields.Char(string='Quantity Backed Unfolded')

    qty_picked = fields.Integer(string='Quantity Picked')
    picked_weight = fields.Float(string='Weight Picked')
    xx_qty_picked = fields.Char(string='Quantity Picked Unfolded')

    qty_stock = fields.Float(string='Quantity Stocked', related='product_id.qty_available')
    qty_stock_rel = fields.Float(string='Quantity Stocked', related='qty_stock', store=True)

    panel_id = fields.Many2one('tokiku.panel', string='Panel', delete='cascade', required=True)

    mold_drawing_trial_date = fields.Char(string='Mold Drawing Trail Date', compute='_compute_mold_drawing_trial_date',
                                          store=True)
    mold_drawing_signing_date = fields.Char(string='Mold Drawing Signing Date',
                                            compute='_compute_mold_drawing_signing_date', store=True)
    mold_drawing_status = fields.Char(string='Mold Draw Status', compute='_compute_mold_drawing_status', store=True)
    material_actual_delivery_date = fields.Char(string='Material Actual Delivery Date',
                                                compute='_compute_material_actual_delivery_date', store=True)
    material_signing_date = fields.Char(string='Material Signing Date', compute='_compute_material_signing_date',
                                        store=True)
    material_status = fields.Char(string='Material Status', compute='_compute_material_status', store=True)

    order_num = fields.Char('Order Number', compute='_compute_order_num', store=True)
    date_order = fields.Char('Date Order', compute='_compute_date_order', store=True)
    mold_expected_arrival_date = fields.Char('Mold Exp Arrival Date')
    material_expected_delivery_date = fields.Char('Material Exp Delivery Date', )
    product_write_date = fields.Datetime(string='Last Updated Date',
                                         compute='_compute_product_write_date')  # related='product_id.write_date')
    product_write_uid = fields.Many2one(string='Last Updated UID', related='product_id.write_uid')
    remark = fields.Char('Remark', related='product_id.remarks')

    material_sum_name = fields.Char('Material Sum Name')
    prod_categ_id = fields.Many2one('product.category', string='Item')
    categ_name = fields.Char('Category', related='product_id.categ_id.name')

    # 鋁外管控表新增欄位
    area = fields.Float('Total Area')#, compute='_compute_area', store=True)
    order_unit = fields.Char('Order Unit')

    # # 出貨狀況
    ship_qty = fields.Integer('Ship Qty')
    ship_weight = fields.Float('Ship Weight')
    un_ship_qty = fields.Integer('Unship Qty')
    xx_ship_qty = fields.Char('Supplier')
    xx_ship_location_qty = fields.Char('Supplier')

    # # 毛料出貨狀況
    raw_un_ship_qty = fields.Integer('Raw Unship Qty', compute='_compute_raw_qty')#, store=True)
    raw_un_ship_weight = fields.Float('Raw Unship Weight', compute='_compute_raw_qty')#, store=True)
    raw_ship_qty = fields.Integer('Raw Ship Qty', compute='_compute_raw_qty')#, store=True)
    raw_ship_weight = fields.Float('Raw Ship Weight', compute='_compute_raw_qty')#, store=True)

    # # 加工訂單
    qty_refine_order = fields.Integer('Qty Total')
    weight_refine_order = fields.Float('Weight Total')
    unit_refine_order = fields.Char('Unit Paint')
    not_refine_order_qty = fields.Integer('Not Order Qty')
    xx_refine_order_qty = fields.Char('Supplier')

    # refine_picking_id
    # 加工登記
    refined_qty = fields.Float(string='Refined Qty')  #, compute='_compute_refined_qty')
    refine_order_qty = fields.Float(string='Refine Order Qty')  # , compute='_compute_refine_order_qty')
    heat_order_qty = fields.Float(string='Heat Order Qty')  # , compute='_compute_heat_order_qty')
    paint_order_qty = fields.Float(string='Paint Order Qty')  # , compute='_compute_paint_order_qty')
    refined_weight = fields.Float(
        string='Refined Weight')  # , compute='_compute_refined_qty',store=True)  # compute='_compute_refined_weight'
    un_refined_qty = fields.Float(string='Un-refined Qty')  # , compute='_compute_refined_qty', store=True)
    xx_qty_refine = fields.Char('Supplier')

    # # 加工登記-出貨
    ship_qty_refine = fields.Integer('Ship Qty')  # , compute='_compute_refined_qty')
    refine_percent = fields.Char('%')#, compute='_compute_percent')
    ship_weight_refine = fields.Float('Ship Weight')  # , compute='_compute_refined_qty', store=True)
    wait_ship_refine_qty = fields.Integer('Wait Ship Qty')  # , compute='_compute_refined_qty', store=True)
    un_ship_refine_qty = fields.Integer('Unship Qty')  # , compute='_compute_refined_qty', store=True)
    unit_refine = fields.Char('Unit')
    xx_qty_refine_ship = fields.Char('Supplier')  # , compute='_compute_refined_qty', store=True)

    # # 熱處理訂單
    qty_heat = fields.Integer('Qty Total')  # , compute='_compute_heat_qty', store=True)
    weight_heat = fields.Float('Weight Total')  # , compute='_compute_heat_qty', store=True)
    not_heat_order_qty = fields.Integer('Not Order Qty')  # , compute='_compute_heat_qty', store=True)

    # # 熱處理登記-出貨
    ship_qty_heat = fields.Integer('Ship Qty')  # , compute='_compute_heat_qty', store=True)
    heat_percent = fields.Char('%')#, compute='_compute_percent')
    ship_weight_heat = fields.Float('Ship Weight')  # , compute='_compute_heat_qty', store=True)
    un_ship_heat = fields.Integer('Unship Qty')  # , compute='_compute_heat_qty', store=True)

    heat_to_assembly = fields.Integer('Heat to Assembly')  # , compute='_compute_heat_qty', store=True)
    heat_to_paint = fields.Integer('Heat to Paint')  # , compute='_compute_heat_qty', store=True)

    # # 烤漆訂單
    qty_paint = fields.Integer('Qty Total')#, compute='_compute_paint_qty')
    weight_paint = fields.Float('Weight Total')#, compute='_compute_paint_qty')
    unit_paint = fields.Char('Unit')
    not_paint_order_qty = fields.Integer('Not Order Qty')#, compute='_compute_paint_qty')
    xx_qty_paint_order = fields.Char('Supplier')#, compute='_compute_paint_qty')

    # # 烤漆出貨
    ship_qty_paint = fields.Integer('Ship Qty')#, compute='_compute_paint_qty')
    ship_weight_paint = fields.Float('Ship Weight')#, compute='_compute_paint_qty')
    un_ship_paint_qty = fields.Integer('Unship Qty')#, compute='_compute_paint_qty')
    unit_ship_paint = fields.Char('Unit')

    # # 烤漆出貨 組裝
    paint_to_assembly_qty = fields.Integer('Ship Qty')#, compute='_compute_paint_qty')
    paint_to_assembly_percent = fields.Char('%')#, compute='_compute_percent')
    paint_to_assembly_weight = fields.Float('Ship Weight')
    paint_to_assembly_unit = fields.Char('Unit')

    # # 烤漆出貨 工地
    paint_to_site_qty = fields.Integer('Ship Qty')#, compute='_compute_paint_qty')
    paint_to_site_percent = fields.Char('%', compute='_compute_percent')
    paint_to_site_weight = fields.Float('Ship Weight')
    paint_to_site_unit = fields.Char('Unit')

    # # 組裝廠
    qty_receive_assembly = fields.Integer('Qty Receive Assembly', compute='_compute_qty_receive_assembly')
    qty_unstock_assembly = fields.Integer('Qty Unstock Assembly')#, compute='_compute_qty_receive_assembly')
    xx_received_assembly = fields.Char('Supplier')

    # # 工地
    qty_receive_site = fields.Integer('Qty Receive Site')#, compute='_compute_qty_receive_site')
    qty_unstock_site = fields.Integer('Qty Unstock Site')#, compute='_compute_qty_receive_site')
    xx_received_site = fields.Char('Supplier')

    # 加工廠退貨
    return_qty_refine = fields.Integer('Qty Total', compute='_compute_return_qty', store=True)
    return_weight_refine = fields.Float('Weight Total', compute='_compute_return_qty', store=True)

    # 熱處理退貨
    return_qty_heat = fields.Integer('Qty Total', compute='_compute_return_qty', store=True)
    return_weight_heat = fields.Float('Weight Total', compute='_compute_return_qty', store=True)

    # 烤漆廠退貨
    return_qty_paint = fields.Integer('Qty Total', compute='_compute_return_qty', store=True)
    return_weight_paint = fields.Float('Weight Total', compute='_compute_return_qty', store=True)

    # 組裝廠退貨
    return_qty_assembly = fields.Integer('Qty Total')#, compute='_compute_return_qty', store=True)
    return_weight_assembly = fields.Float('Weight Total')#, compute='_compute_return_qty', store=True)

    return_qty_site = fields.Integer('Qty Total')  # , compute='_compute_return_qty', store=True)
    return_weight_site = fields.Float('Weight Total')  # , compute='_compute_return_qty', store=True)

    # # 鋁擠型外退貨
    xx_return_qty = fields.Char('Warehouse')
    # # 鋁擠型外收貨
    xx_received_qty = fields.Char('Warehouse')
    # # 鋁擠型外扣款
    xx_deduction = fields.Char('Warehouse')
    # # 鋁擠型外退貨結案
    xx_return_closed = fields.Char('Warehouse')

    # # 鋁外庫存狀況
    stock_paint = fields.Integer('Qty Total Paint')
    stock_assembly = fields.Integer('Qty Total Assembly')
    stock_site = fields.Integer('Qty Total Site')
    xx_stock_paint = fields.Char('Warehouse')

    # # 鋁外庫存盤點
    xx_stock_qty = fields.Char('Warehouse')

    # # 鋁外實際庫存狀況
    actual_stock_paint = fields.Integer('Qty Total Paint')
    actual_stock_assembly = fields.Integer('Qty Total Assembly')
    actual_stock_site = fields.Integer('Qty Total Site')
    xx_actual_stock = fields.Char('Warehouse')
    qty_cut_done = fields.Integer('Qty Total')  # , compute='_compute_cutdone_qty')

    @api.multi
    def _compute_raw_qty(self):
        for rec in self:
            cut_quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.name == 'Stock')

            rec.raw_ship_qty = 0

            total_qty = 0
            ship_qty = 0
            done_qty = 0
            for q in cut_quants:
                if q.panel_line_id.default_code == rec.default_code:
                    done_qty += q.qty
                    if q.qty > 0:
                        total_qty += q.qty
                    else:
                        ship_qty += (q.qty * -1)

                rec.raw_ship_qty = total_qty
            rec.raw_ship_weight = round(rec.raw_ship_qty * rec.weight * (rec.cutting_length / 1000.0), 3)
            rec.raw_un_ship_qty = rec.total_ordered_qty - rec.raw_ship_qty
            rec.raw_un_ship_weight = round(rec.raw_un_ship_qty * rec.weight * (rec.cutting_length / 1000.0), 3)
    @api.multi
    @api.depends('product_id.stock_move_ids')
    def _compute_return_qty(self):
        for rec in self:
            return_picking_line = self.env['stock.return.picking.line'].search([('product_id', '=', rec.product_id.id)])
            for line in return_picking_line:
                if line.with_context(lang=None).move_id.location_id.location_id.name == 'Refine' and line.move_id.atlas_id == rec.atlas_id:
                    rec.return_qty_refine += line.quantity
                    rec.return_weight_refine += round(rec.return_qty_refine * rec.weight * (rec.cutting_length / 1000.0), 3)
                elif line.with_context(lang=None).move_id.location_id.location_id.name == 'Heat' and line.move_id.atlas_id == rec.atlas_id:
                    rec.return_qty_heat += line.quantity
                    rec.return_weight_heat += round(
                        rec.return_qty_heat * rec.weight * (rec.cutting_length / 1000.0), 3)
                elif line.with_context(lang=None).move_id.location_id.location_id.name == 'Paint' and line.move_id.atlas_id == rec.atlas_id:
                    rec.return_qty_paint += line.quantity
                    rec.return_weight_paint += round(
                        rec.return_qty_paint * rec.weight * (rec.cutting_length / 1000.0), 3)

    @api.multi
    def _compute_percent(self):
        for rec in self:
            if rec.demand_qty == 0:
                rec.paint_to_site_qty = 0
                rec.paint_to_assembly_percent = 0
                rec.refine_percent = 0
                rec.heat_percent = 0
            else:
                percent_paint_to_site = (rec.paint_to_site_qty / rec.demand_qty) * 100
                rec.paint_to_site_percent = str(percent_paint_to_site) + '%'
                percent_paint_to_assembly = (rec.paint_to_assembly_qty / rec.demand_qty) * 100
                rec.paint_to_assembly_percent = str(percent_paint_to_assembly) + '%'
                percent_refine = (rec.ship_qty_refine / rec.demand_qty) * 100
                rec.refine_percent = str(percent_refine) + '%'
                percent_heat = (rec.ship_qty_heat / rec.demand_qty) * 100
                rec.heat_percent = str(percent_heat) + '%'

    @api.multi
    # @api.depends ('project_id', 'categ_id', 'name', 'default_code', 'product_id')  # 'category_code',
    def _compute_mold_id(self):
        for rec in self:
            if rec.prod_categ_id.code == 'aluminum':
                mold = self.env['product.product'].search(
                    [('category_code', '=', 'mold'),
                     ('default_code', '=', rec.code)], limit=1)
                if mold:
                    rec.mold_id = mold.id
            elif rec.prod_categ_id.code == 'raw':
                mold = self.env['product.product'].search(
                    [('category_code', '=', 'mold'),
                     ('default_code', '=', rec.default_code)], limit=1)
                if mold:
                    rec.mold_id = mold.id

    @api.multi
    # @api.depends('panel_id.order_ids', 'panel_id.order_ids.state', 'panel_id.order_line_ids')
    def _compute_order_lines(self):
        for rec in self:
            rec.order_line_ids = rec.panel_id.order_line_ids.filtered(lambda x: x.product_id.id == rec.product_id.id and
                                                                                x.atlas_id.id == rec.atlas_id.id and
                                                                                x.state in ['purchase', 'done'])

    @api.multi
    @api.depends('seller_id.weight')
    def _compute_mold_weight(self):
        for rec in self:
            rec.mold_weight = round(rec.seller_id.weight, 3)

    @api.multi
    @api.depends('order_line_ids', 'product_id.mold_id', 'product_id.mold_id.seller_ids',
                 'product_id.mold_id.seller_ids.weight',
                 'product_id.mold_id.seller_ids.product_material', 'product_id.mold_id.seller_ids.name')
    def _compute_weight(self):
        for rec in self:
            sellers = []
            if rec.panel_id.categ_code == 'aluminum':
                sellers = rec.product_id.mold_id.seller_ids.filtered(
                    lambda x: x.product_material == rec.material and x.name.id in [l.order_id.partner_id.id for l in
                                                                                   rec.order_line_ids])
            elif rec.panel_id.categ_code == 'raw':
                sellers = rec.product_id.mold_id.seller_ids.filtered(
                    lambda x: x.product_material == rec.material and x.name.id == rec.supplier_name.id)
            if not sellers:
                rec.weight = 0
                for l in rec.order_line_ids:
                    if l.unit_weight > 0:
                        rec.weight = l.unit_weight
                        break
            else:
                for s in sellers:
                    rec.weight = s.weight
                    rec.mold_seller_id = s.name
                    # break

    @api.multi
    @api.depends('weight', 'order_line_ids')
    def _compute_mold_seller_id(self):
        for rec in self:
            sellers = []
            if rec.panel_id.categ_code == 'aluminum':
                sellers = rec.product_id.mold_id.seller_ids.filtered(
                    lambda x: x.product_material == rec.material and x.name.id in [l.order_id.partner_id.id for l in
                                                                                   rec.order_line_ids])
            elif rec.panel_id.categ_code == 'raw':
                sellers = rec.product_id.mold_id.seller_ids.filtered(
                    lambda x: x.product_material == rec.material and x.name.id == rec.supplier_name.id)
            # print ("sellers %s" % sellers)
            if sellers:
                for s in sellers:
                    rec.mold_seller_id = s.name.id
                    break

    @api.multi
    @api.depends('seller_id.coating')
    def _compute_coating(self):
        for rec in self:
            rec.coating = round(rec.seller_id.coating, 3)

    @api.multi
    @api.depends('product_id.paint_area')
    def _compute_paint_area(self):
        for rec in self:
            rec.paint_area = rec.product_id.paint_area

    @api.multi
    @api.depends('cutting_length', 'cutting_width')
    def _compute_unit_area(self):
        for rec in self:
            rec.unit_area = round(rec.cutting_length / 1000 * rec.cutting_width / 1000, 3)

    @api.multi
    @api.depends('product_id.mold_id', 'product_id.seller_ids')
    def _compute_area(self):
        for rec in self:
            rec.area = rec.product_id.paint_area
            # paint_area = self.env['product.product'].search([('default_code', '=', rec.code),
            #                                                  ])
            # for l in paint_area:
            #     rec.area = l.paint_area
            if rec.panel_id.categ_code == 'plate' or rec.panel_id.categ_code == 'glass' or rec.panel_id.categ_code == 'steel':
                rec.area = (rec.cutting_length * rec.cutting_width)/1000000 * rec.demand_qty

    @api.multi
    # @api.depends('atlas_id', 'product_id', 'product_id.stock_quant_ids.qty', 'product_id.stock_move_ids.state')
    def _compute_cutdone_qty(self):
        for rec in self:
            cut_quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.name == 'Stock')

            rec.qty_cut_done = 0

            total_qty = 0
            ship_qty = 0
            done_qty = 0
            for q in cut_quants:
                if q.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    done_qty += q.qty
                    if q.qty > 0:
                        total_qty += q.qty
                    else:
                        ship_qty += (q.qty * -1)

            rec.qty_cut_done = ship_qty

    @api.multi
    # @api.depends('atlas_id', 'product_id', 'product_id.stock_quant_ids.qty', 'product_id.stock_move_ids.state')
    def _compute_paint_qty(self):
        for rec in self:
            paint_quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.name == 'Done' and x.location_id.location_id.name == 'Paint')
            assembly_quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(lambda
                                                                                                  x: x.propagated_from_id.location_id.location_id.name == 'Paint' and x.propagated_from_id.location_id.name == 'Done' and x.location_id.name == 'Pending' and x.location_id.location_id.name == 'Assembly')
            site_quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(lambda
                                                                                              x: x.propagated_from_id.location_id.location_id.name == 'Paint' and x.propagated_from_id.location_id.name == 'Done' and x.location_id.location_id.name == 'Site')

            rec.qty_paint = 0
            rec.weight_paint = 0
            rec.not_paint_order_qty = 0

            total_qty = 0
            ship_qty = 0
            done_qty = 0
            for q in paint_quants:
                if q.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    done_qty += q.qty
                    if q.qty > 0:
                        total_qty += q.qty
                    else:
                        ship_qty += (q.qty * -1)

            rec.qty_paint = total_qty
            rec.weight_paint = round(rec.qty_paint * rec.weight * (rec.cutting_length / 1000.0), 3)
            if rec.surface_coating and rec.surface_coating != "''":
                rec.not_paint_order_qty = rec.total_ordered_qty - total_qty

            paint2ssembly = 0
            for aq in assembly_quants:
                if aq.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    if aq.qty > 0:
                        paint2ssembly += aq.qty

            rec.paint_to_assembly_qty = paint2ssembly
            rec.paint_to_assembly_weight = round(rec.paint_to_assembly_qty * rec.weight * (rec.cutting_length / 1000.0),
                                                 3)

            paint2site = 0
            for sq in site_quants:
                if sq.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    if sq.qty > 0:
                        paint2site += sq.qty

            rec.paint_to_site_qty = paint2site
            rec.paint_to_site_weight = round(rec.paint_to_site_qty * rec.weight * (rec.cutting_length / 1000.0), 3)

    @api.multi
    # @api.depends('atlas_id', 'product_id', 'product_id.stock_quant_ids.qty', 'product_id.stock_move_ids.state',
    #              'ship_qty_refine')
    def _compute_qty_receive_assembly(self):
        for rec in self:
            quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.location_id.name == 'Assembly')

            total_qty = 0
            ship_qty = 0
            done_qty = 0
            for q in quants:
                if q.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    done_qty += q.qty
                    if q.qty > 0:
                        total_qty += q.qty
                    else:
                        ship_qty += (q.qty * -1)
            rec.qty_receive_assembly = total_qty
            rec.qty_unstock_assembly = rec.total_ordered_qty - rec.qty_receive_assembly

    @api.multi
    def _compute_qty_receive_site(self):
        for rec in self:
            quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.location_id.name == 'Site' and x.location_id.name == 'Pending')

            total_qty = 0
            ship_qty = 0
            done_qty = 0
            for q in quants:
                if q.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    done_qty += q.qty
                    if q.qty > 0:
                        total_qty += q.qty
                    else:
                        ship_qty += (q.qty * -1)
            rec.qty_receive_site = total_qty
            rec.qty_unstock_site = ship_qty

    @api.multi
    # @api.depends('atlas_id', 'product_id', 'product_id.stock_quant_ids.qty', 'product_id.stock_move_ids.state',
    #              'ship_qty_refine')
    def _compute_heat_qty(self):
        for rec in self:
            quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.name == 'Done' and x.location_id.location_id.name == 'Heat')
            assembly_quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(lambda
                                                                                                  x: x.location_id.location_id.name == 'Assembly' and x.propagated_from_id.location_id.location_id.name == 'Heat' and x.propagated_from_id.location_id.name == 'Done')
            paint_quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(lambda
                                                                                               x: x.location_id.location_id.name == 'Paint' and x.propagated_from_id.location_id.location_id.name == 'Heat' and x.propagated_from_id.location_id.name == 'Done')

            rec.qty_heat = 0
            rec.weight_heat = 0
            rec.not_heat_order_qty = 0
            total_qty = 0
            ship_qty = 0
            done_qty = 0

            for q in quants:
                if q.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    done_qty += q.qty
                    if q.qty > 0:
                        total_qty += q.qty
                    else:
                        ship_qty += (q.qty * -1)

            rec.qty_heat = total_qty
            rec.weight_heat = round(rec.qty_heat * rec.weight * (rec.cutting_length / 1000.0), 3)
            if rec.heating and rec.heating != "''":
                rec.not_heat_order_qty = rec.total_ordered_qty - total_qty

            rec.ship_qty_heat = ship_qty
            rec.ship_weight_heat = round(ship_qty * rec.weight * (rec.cutting_length / 1000.0), 3)
            rec.un_ship_heat = rec.not_heat_order_qty + done_qty
            heat2ssembly = 0
            for aq in assembly_quants:
                if aq.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    if aq.qty > 0:
                        heat2ssembly += aq.qty
            rec.heat_to_assembly = heat2ssembly

            heat2paint = 0
            for pq in paint_quants:
                if pq.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    if pq.qty > 0:
                        heat2paint += pq.qty
            rec.heat_to_paint = heat2paint

    @api.multi
    # @api.depends('atlas_id', 'product_id', 'product_id.stock_quant_ids.qty', 'product_id.stock_move_ids.state')
    def _compute_refined_qty(self):
        for rec in self:
            quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.name == 'Done' and x.location_id.location_id.name == 'Refine')
            total_qty = 0
            ship_qty = 0
            done_qty = 0
            for q in quants:
                if q.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    done_qty += q.qty
                    if q.qty > 0:
                        total_qty += q.qty
                    else:
                        ship_qty += (q.qty * -1)

            rec.refined_qty = total_qty
            rec.refined_weight = round(total_qty * rec.weight * (rec.cutting_length / 1000.0), 3)
            rec.un_refined_qty = rec.total_ordered_qty - rec.refined_qty

            rec.ship_qty_refine = ship_qty
            rec.ship_weight_refine = round(ship_qty * rec.weight * (rec.cutting_length / 1000.0), 3)
            rec.wait_ship_refine_qty = done_qty
            rec.un_ship_refine_qty = rec.un_refined_qty + done_qty

    @api.multi
    # @api.depends('atlas_id', 'product_id', 'product_id.stock_quant_ids.qty', 'product_id.stock_move_ids.state')
    def _compute_refined_pending_qty(self):
        for rec in self:
            quants = rec.with_context(lang=None).product_id.stock_quant_ids.filtered(
                lambda x: x.location_id.name == 'Pending' and x.location_id.location_id.name == 'Refine')
            total_qty = 0
            pending_qty = 0
            for q in quants:
                if q.panel_line_id.atlas_id.id == rec.atlas_id.id:
                    pending_qty += q.qty
                    for h in q.history_ids:
                        if h.product_qty > 0:
                            total_qty += h.product_qty

            rec.refined_pending_qty = total_qty

    @api.multi
    def _compute_refined_weight(self):
        for rec in self:
            product_uom_qty = 0.0
            refine_moves = self.env['stock.move'].sudo().search(
                [('picking_id.contract_id', '=', self.env.user.contract_id.id),
                 ('picking_id.categ_id', '=', rec.panel_id.categ_id.id),
                 ('picking_id.stage', '=', 'refine'),
                 ('picking_id.state', '=', 'draft'),
                 ('location_id.name', '=', 'Pending'),
                 ('location_dest_id.name', '=', 'Done'),
                 ('product_id', '=', rec.product_id.id),
                 ])

            for ml in refine_moves:
                loc = ml.location_id.complete_name
                loc_index = loc.find(u'加工')
                if loc_index != -1:
                    product_uom_qty += ml.product_uom_qty

            if rec.description:
                desc_str = rec.description
                alum_material = self._compute_description_index(desc_str)

    def _compute_description_index(self, desc_str):
        alum_idx = desc_str.find(u'鋁料')
        if alum_idx >= 7:
            material = desc_str[alum_idx - 7:alum_idx]
        return material

    @api.multi
    @api.depends('volume')
    def _compute_length(self):
        for p in self:
            p.length = int(p.volume)

    @api.multi
    @api.depends('order_line_ids', 'weight', 'cutting_length', 'total_ordered_qty', 'rest_demand_qty')
    def _compute_weight_sub(self):
        for p in self:
            if p.demand_qty > 0:
                p.weight_sub = round(((p.weight * p.cutting_length) / 1000) * p.demand_qty, 3)
            p.rest_demand_weight = round(p.rest_demand_qty * p.weight * (p.cutting_length / 1000.0), 3)
            p.order_weight = round(p.total_ordered_qty * p.weight * (p.cutting_length / 1000.0), 3)

    @api.multi
    @api.depends('atlas_demand_qty', 'mold_demand_qty')
    def _compute_demand_qty(self):
        for l in self:
            l.demand_qty = 0
            headers = {}
            demands = {}
            if l.panel_id.categ_id.code == 'mold':
               l.demand_qty = l.mold_demand_qty
               #  if l.qty_stock > l.mold_demand_qty:
               #      l.demand_qty = l.qty_stock - l.mold_demand_qty
               #  else:
               #      l.demand_qty = l.mold_demand_qty

            elif l.panel_id.categ_id.code == 'raw':
                for c in l.panel_id.project_id.contract_ids:
                    for d in c.demand_ids:
                        headers[d.id] = d.name
                        demands[d.id] = 0
                        for dl in d.demand_line_ids.filtered(lambda x: x.product_id.id == l.product_id.id):
                            l.demand_qty += parse_float(dl.qty)
                            demands[d.id] += parse_float(dl.qty)
            else:
                l.demand_qty = l.atlas_demand_qty

    @api.multi
    # @api.depends('order_line_ids.qty_received')
    def _compute_qty_received(self):
        for rec in self:
            rec.qty_received = 0
            for l in rec.order_line_ids.filtered(lambda x: x.state in ['purchase', 'done']):
                rec.qty_received += l.qty_received

    @api.multi
    # @api.depends('panel_id.order_ids', 'panel_id.order_ids.state', 'order_line_ids', 'order_line_ids.product_qty')
    def _compute_refine_order_qty(self):
        for rec in self:
            for o in rec.panel_id.order_ids.filtered(lambda x: x.stage == 'refine' and x.state in ['purchase', 'done']):
                for l in o.order_line.filtered(
                        lambda y: y.default_code == rec.default_code and y.atlas_id.id == rec.atlas_id.id):
                    rec.refine_order_qty += l.order_qty

    @api.multi
    # @api.depends('panel_id.order_ids', 'panel_id.order_ids.state', 'order_line_ids', 'order_line_ids.product_qty')
    def _compute_heat_order_qty(self):
        for rec in self:
            for o in rec.panel_id.order_ids.filtered(lambda x: x.stage == 'heat' and x.state in ['purchase', 'done']):
                for l in o.order_line.filtered(lambda y: y.default_code == rec.default_code and
                                                         y.atlas_id.id == rec.atlas_id.id):
                    rec.heat_order_qty += l.order_qty

    @api.multi
    # @api.depends('panel_id.order_ids', 'panel_id.order_ids.state', 'order_line_ids', 'order_line_ids.product_qty')
    def _compute_paint_order_qty(self):
        for rec in self:
            for o in rec.panel_id.order_ids.filtered(lambda x: x.stage == 'paint' and x.state in ['purchase', 'done']):
                for l in o.order_line.filtered(lambda y: y.default_code == rec.default_code and
                                                         y.atlas_id.id == rec.atlas_id.id):
                    rec.paint_order_qty += l.order_qty

    @api.multi
    def act_raw_demand_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_line_raw_demand_qty')[1]
        return {
            'name': "Demand Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'tokiku.demand_line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            # 'flags': {'tree': {'headless': False}},
            'domain': [
                ('name', '=', self.default_code),
                ('supplier_part_no', '=', self.supplier_part_no),
                ('order_length', '=', self.length),
                ('product_id.id', '=', self.product_id.id),
            ],
            # 'context': {'search_default_groupby_supplier': 1},
        }

    @api.multi
    def act_order_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_line_order_qty')[1]
        return {
            'name': "Order Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order.line',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [('panel_line_id', '=', self.id),
                       ('stage_code', '=', 'material'),
                       ('state', '=', 'purchase'),
                       ],
        }

    @api.multi
    def act_raw_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_line_raw_qty')[1]
        location_dest_id = self.env['stock.location'].with_context(lang=None).search(
                    [('usage', '=', 'internal'),
                     ('name', '=', 'Stock')], limit=1)

        return {
            'name': "Raw Qty Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('new_default_code', '=', self.default_code),
                ('location_dest_id', '=', location_dest_id.id),
                ('product_id', '=', self.product_id.id),
            ],
        }

    @api.multi
    def act_refined_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_refined_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_refine_pending')
        stock_location_refine_pending = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_refine_done')
        stock_location_refine_done = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_refine_pending.id),
                ('location_dest_id', '=', stock_location_refine_done.id),
            ],
        }

    @api.multi
    def act_ship_qty_refine(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_ship_qty_refine')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_refine_done')
        stock_location_refine_done = self.env[res_model_pending].browse(res_id_pending)

        # res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku','stock_location_refine_done')
        # stock_location_refine_done = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_refine_done.id),
                # ('location_dest_id', '=', stock_location_refine_done.id),
            ],
        }

    @api.multi
    def act_qty_heat(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_refined_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_heat_pending')
        stock_location_heat_pending = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_heat_done')
        stock_location_heat_done = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_heat_pending.id),
                ('location_dest_id', '=', stock_location_heat_done.id),
            ],
        }

    @api.multi
    def act_ship_qty_heat(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_refined_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_heat_done')
        stock_location_heat_done = self.env[res_model_pending].browse(res_id_pending)

        # res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku','stock_location_heat_done')
        # stock_location_heat_done = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_heat_done.id),
                # ('location_dest_id', '=', stock_location_heat_pending.id),
            ],
        }

    @api.multi
    def act_heat_to_assembly(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_refined_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_heat_done')
        stock_location_heat_done = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_assembly_pending')
        stock_location_assembly_pending = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_heat_done.id),
                ('location_dest_id', '=', stock_location_assembly_pending.id),
            ],
        }

    @api.multi
    def act_heat_to_paint(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_refined_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_heat_done')
        stock_location_heat_done = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_paint_pending')
        stock_location_paint_pending = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_heat_done.id),
                ('location_dest_id', '=', stock_location_paint_pending.id),
            ],
        }

    @api.multi
    def act_qty_paint(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_refined_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_paint_pending')
        stock_location_paint_pending = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_paint_done')
        stock_location_paint_done = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_paint_pending.id),
                ('location_dest_id', '=', stock_location_paint_done.id),
            ],
        }

    @api.multi
    def act_paint_to_assembly_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_refined_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_paint_done')
        stock_location_paint_done = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_assembly_pending')
        stock_location_assembly_pending = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_paint_done.id),
                ('location_dest_id', '=', stock_location_assembly_pending.id),
            ],
        }

    @api.multi
    def act_paint_to_site_qty(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_paint_to_site_qty')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                           'stock_location_paint_done')
        stock_location_paint_done = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_site_pending')
        stock_location_site_pending = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                ('location_id', '=', stock_location_paint_done.id),
                ('location_dest_id', '=', stock_location_site_pending.id),
            ],
        }

    @api.multi
    def act_qty_receive_assembly(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_paint_to_site_qty')[1]

        # res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku','stock_location_site_pending')
        # stock_location_site_pending = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_assembly_pending')
        stock_location_assembly_pending = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                # ('location_id', '=', stock_location_site_pending.id),
                ('location_dest_id', '=', stock_location_assembly_pending.id),
            ],
        }

    @api.multi
    def act_qty_receive_site(self, values):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_stock_picking_qty_receive_site')[1]

        res_model_pending, res_id_pending = self.env['ir.model.data'].get_object_reference('tokiku','stock_location_site_pending')
        stock_location_site_pending = self.env[res_model_pending].browse(res_id_pending)

        res_model_done, res_id_done = self.env['ir.model.data'].get_object_reference('tokiku',
                                                                                     'stock_location_site_done')
        stock_location_site_done = self.env[res_model_done].browse(res_id_done)

        return {
            'name': "Stock Moves Lines",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'domain': [
                ('atlas_id', '=', self.atlas_id.id),
                ('default_code', '=', self.default_code),
                # ('location_id', '=', stock_location_site_pending.id),
                ('location_dest_id', '=', stock_location_site_pending.id),
            ],
        }

    @api.multi
    # @api.depends('panel_id.order_ids', 'panel_id.order_ids.state', 'order_line_ids', 'order_line_ids.product_qty')
    def _compute_order_qty(self):
        for rec in self:
            rec.order_qty = 0
            rec.spare_qty = 0
            rec.qty_backorder = 0
            headers = {}
            qty = {}
            partners = {}

            for o in rec.panel_id.order_ids.filtered(
                    lambda
                            x: x.categ_id.id == rec.panel_id.categ_id.id and x.stage == 'material' and x.state in [
                        'purchase', 'done']):
                headers[o.partner_id.id] = o.partner_id.ref
                qty[o.partner_id.id] = 0
                partners[o.partner_id.id] = ''

            for l in rec.order_line_ids.filtered(
                    lambda x: x.state in ['purchase', 'done'] and x.stage_code == 'material'
                              and rec.product_id.id == x.product_id.id):
                rec.order_qty += l.qty_normal
                rec.spare_qty += l.spare_qty
                rec.qty_backorder += l.qty_back_order
                key = l.order_id.partner_id.id
                qty[key] += l.product_qty
                if rec.panel_id.categ_id.code in ['raw', 'aluminum']:  # and rec.weight
                    partners[key] = u"%d ( %s kg)" % (
                        qty[key], round(qty[key] * rec.weight * (rec.cutting_length / 1000.0), 3))
                else:
                    partners[key] = qty[key]

            rec.total_ordered_qty = rec.order_qty + rec.spare_qty + rec.qty_backorder
            rec.xx_order_qty = json.dumps([headers, partners])

    @api.multi
    def _compute_rest_demand_qty(self):
        for rec in self:
            rec.rest_demand_qty = rec.demand_qty - rec.total_ordered_qty
            if rec.rest_demand_qty < 0:
                rec.rest_demand_qty = 0

    # @api.multi
    # @api.depends('order_qty', 'spare_qty', 'qty_backorder')
    # def _compute_total_ordered_qty(self):
    #     for rec in self:
    #         rec.total_ordered_qty = rec.order_qty + rec.spare_qty + rec.qty_backorder

    @api.multi
    def compute_qty_returned(self):
        for l in self:
            l.qty_returned = 0
            headers = {}
            pickings = {}
            for p in l.panel_id.project_id.picking_ids.filtered(lambda x: x.picking_type_code == 'outgoing'):
                if p.date_done and len(p.date_done) > 10:
                    c_key = p.date_done[:10]
                    if not headers.get(c_key):
                        headers[c_key] = "%s.%s" % (c_key.split('-')[1], c_key.split('-')[2])
                        pickings[c_key] = 0
                    for ml in p.move_lines.filtered(
                            lambda x: x.origin_returned_move_id and x.product_id.id == l.product_id.id):
                        l.qty_returned += ml.product_qty
                        pickings[c_key] += ml.product_qty
            l.xx_qty_returned = json.dumps([headers, pickings])

    @api.multi
    def compute_qty_picked(self):
        for l in self:
            l.qty_picked = 0
            headers = {}
            pickings = {}
            for p in l.panel_id.project_id.picking_ids.filtered(lambda x: x.picking_type_code == 'internal'):
                if p.date_done and len(p.date_done) > 10:
                    c_key = p.date_done[:10]
                    if not headers.get(c_key):
                        headers[c_key] = "%s.%s" % (c_key.split('-')[1], c_key.split('-')[2])
                        pickings[c_key] = 0
                    for ml in p.move_lines.filtered(
                            lambda x: not x.origin_returned_move_id and x.product_id.id == l.product_id.id):
                        l.qty_picked += ml.product_qty
                        pickings[c_key] += ml.product_qty
            l.xx_qty_picked = json.dumps([headers, pickings])

    def compute_qty_backed(self):
        for l in self:
            l.qty_backed = 0
            headers = {}
            pickings = {}
            for p in l.panel_id.project_id.picking_ids.filtered(lambda x: x.picking_type_code == 'incoming'):
                if p.date_done and len(p.date_done) > 10:
                    c_key = p.date_done[:10]
                    if not headers.get(c_key):
                        headers[c_key] = "%s.%s" % (c_key.split('-')[1], c_key.split('-')[2])
                        pickings[c_key] = 0
                    for ml in p.move_lines.filtered(
                            lambda x: x.origin_returned_move_id and x.product_id.id == l.product_id.id):
                        l.qty_backed += ml.product_qty
                        pickings[c_key] += ml.product_qty
            l.xx_qty_backed = json.dumps([headers, pickings])

    @api.multi
    @api.depends('product_id.qty_available')
    def _compute_stock(self):
        for l in self:
            l.qty_stock = int(l.product_id.qty_available)

    # @api.multi
    # @api.depends('demand_qty', 'order_qty', 'qty_backorder', 'total_ordered_qty')
    # def _compute_rest_demand_qty(self):
    #     for p in self:
    #         # + (p.qty_stock - p.qty_received)
    #         p.rest_demand_qty = p.demand_qty - p.total_ordered_qty
    #         if p.rest_demand_qty < 0:
    #             p.rest_demand_qty = 0

    @api.multi
    @api.depends('product_id', 'product_id.mold_drawing_info_ids',
                 'product_id.mold_drawing_info_ids.mold_drawing_trial_date')
    def _compute_mold_drawing_trial_date(self):
        for rec in self:
            rec.mold_drawing_trial_date = ', '.join(
                [m.mold_drawing_trial_date for m in rec.product_id.mold_drawing_info_ids])

    @api.multi
    @api.depends('product_id', 'product_id.mold_drawing_info_ids',
                 'product_id.mold_drawing_info_ids.mold_drawing_signing_date')
    def _compute_mold_drawing_signing_date(self):
        for rec in self:
            rec.mold_drawing_signing_date = ', '.join(
                [m.mold_drawing_signing_date for m in rec.product_id.mold_drawing_info_ids])

    @api.multi
    @api.depends('product_id', 'product_id.mold_drawing_info_ids',
                 'product_id.mold_drawing_info_ids.mold_drawing_status')
    def _compute_mold_drawing_status(self):
        for rec in self:
            rec.mold_drawing_status = ''.join(
                [m.mold_drawing_status for m in rec.product_id.mold_drawing_info_ids][-1:])

    @api.multi
    @api.depends('product_id.material_section_info_ids')
    def _compute_material_actual_delivery_date(self):
        for rec in self:
            rec.material_actual_delivery_date = ', '.join(
                [m.actual_delivery_date for m in rec.product_id.material_section_info_ids])

    @api.multi
    @api.depends('product_id.material_section_info_ids')
    def _compute_material_signing_date(self):
        for rec in self:
            rec.material_signing_date = ', '.join([m.signing_date for m in rec.product_id.material_section_info_ids])

    @api.multi
    @api.depends('product_id.material_section_info_ids')
    def _compute_material_status(self):
        for rec in self:
            rec.material_status = ''.join(
                [m.material_section_status for m in rec.product_id.material_section_info_ids][-1:])

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

    @api.multi
    # @api.depends('order_line_ids', 'panel_id.order_ids')
    def _compute_order_num(self):
        for rec in self:
            rec.order_num = ', '.join(set([l.order_id.name for l in rec.order_line_ids]))

    @api.multi
    # @api.depends('order_line_ids')
    def _compute_date_order(self):
        fmt = '%Y-%m-%d %H:%M:%S'
        user_time_zone = pytz.UTC

        if self.env.user.partner_id.tz:
            user_time_zone = pytz.timezone(self.env.user.partner_id.tz)

        for rec in self:
            for l in rec.order_line_ids:
                date_order = l.order_id.date_order
                user_time = datetime.strptime(date_order, fmt)
                user_time = pytz.utc.localize(user_time).astimezone(user_time_zone)
                rec.date_order = user_time.strftime(fmt)

    @api.multi
    def _compute_product_write_date(self):
        fmt = '%Y-%m-%d %H:%M:%S'
        user_time_zone = pytz.UTC

        if self.env.user.partner_id.tz:
            user_time_zone = pytz.timezone(self.env.user.partner_id.tz)

        for rec in self:
            if rec.product_id.write_date:
                user_time = datetime.strptime(rec.product_id.write_date, fmt)
                user_time = pytz.utc.localize(user_time).astimezone(user_time_zone)
                rec.product_write_date = user_time.strftime(fmt)


class AssemblyPanelLine(models.Model):
    _name = 'tokiku.assembly_panel_line'  # Object defined in Panel Class

    # name = fields.Char(string='Name', related='bom_id.product_id.name')
    # partner_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory', change_default=False) #組裝廠
    # building_demand_ids = fields.One2many('tokiku.building.demands', 'assembly_panel_line_id')
    # bom_id = fields.Char(string='BOM Number', related='atlas_line.bom_no')  # 組合編號

    atlas_line = fields.Many2one('tokiku.atlas_line')  # Reference to objects in atlas_line class
    panel_id = fields.Many2one('tokiku.panel', string='Assembly Panel')  # Reference to Panel Class
    supplier_id = fields.Many2one('tokiku.supplier_info', string='Assembly Partner')  # 組裝廠
    supplier_name = fields.Char(related='supplier_id.supplier_id.ref', string='Assembly Partner')
    atlas_id = fields.Many2one('tokiku.atlas', string='Atlas Name')  # 加工圖集
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別
    bom_id = fields.Many2one('mrp.bom', string='BOM Number')  # 組合編號
    assembly_section = fields.Char(string='Assembly Section')
    product_name = fields.Char(related='bom_id.product_id.name', string='BOM Number')
    default_code = fields.Char(related='bom_id.product_id.default_code', string='BOM Number')

    total_demand = fields.Float(string='Total Demand', digits=(16, 0))  # 需求量
    frame_completed_prep = fields.Integer(string='Frame Completed Prep', compute='_compute_completed_prep',
                                          store=True)  # 框架備料完成
    frame_assembling = fields.Integer(string='Frame Assembling')  # 框架組立中
    frame_assembled = fields.Integer(string='Frame Assembled', compute='_compute_assembled', store=True)  # 框架組裝完成
    frame_unassembled = fields.Integer(string='Frame Unassembled', compute='_compute_unassembled', store=True)  # 框架未組裝
    completed_prep = fields.Integer(string='Completed Prep', compute='_compute_completed_prep', store=True)  # 備料完成
    assembling = fields.Integer(string='Assembling', compute='_compute_assembling', store=True)  # 組立中
    assembled = fields.Integer(string='Assembled', compute='_compute_assembled', store=True)  # 組裝完成
    unassembled = fields.Integer(string='Unassembled', compute='_compute_unassembled', store=True)  # 未組裝
    packaging_qty = fields.Integer(string='Packaging Qty')  # 上架包裝
    shipped_qty = fields.Integer(string='Shipped Qty')  # 出貨完成
    undelivered_qty = fields.Integer(string='Undelivered Qty')  # 未出貨 (the total of both assembled and unassembled)
    pending_shipment = fields.Integer(string='Pending Shipment')  # 待出貨

    # Unique to Assembly Preparation
    frame_scheduled_assembly_qty = fields.Integer(string='Frame Scheduled Assembly Qty',
                                                  compute='_compute_assembly_qty', store=True)  # 框架預定可組數
    scheduled_assembly_qty = fields.Integer(string='Scheduled Assembly Qty', compute='_compute_assembly_qty',
                                            store=True)  # 預定可組數
    frame_incomplete_prep = fields.Integer(string='Frame Incomplete Prep', compute='_compute_incomplete_prep',
                                           store=True)  # 未備料數
    incomplete_prep = fields.Integer(string='Incomplete Prep', compute='_compute_incomplete_prep', store=True)  # 未備料數
    remark = fields.Char(string='Remark')  # 備註

    # Summary 總表
    summary_content = fields.Char(string='Summary Content')  # 內容
    frame_comp_rate = fields.Char(string='Frame Complete Rate', compute='_compute_comp_rate', store=True)  # 框架完成率
    complete_rate = fields.Char(string='Complete Rate', compute='_compute_comp_rate', store=True)  # 完成率
    shipping_comp_rate = fields.Char(string='Shipping Complete Rate', compute='_compute_comp_rate', store=True)  # 出貨完成率

    # production_ids = fields.One2many('mrp.production', 'assembly_panel_line_id')

    assembly_order_line_ids = fields.One2many('tokiku.assembly_order_line', 'assembly_panel_line_id')
    production_record_line_ids = fields.One2many('tokiku.production_record_line', 'assembly_panel_line_id')

    production_id = fields.Many2one('mrp.production', delete='cascade')
    frame_production_id = fields.Many2one('mrp.production', delete='cascade')

    @api.multi
    @api.depends('production_record_line_ids', 'production_record_line_ids.prepared_qty')
    def _compute_completed_prep(self):
        for l in self:
            frame_qty = 0
            surface_qty = 0
            for pl in l.production_record_line_ids.filtered(lambda x: x.production_record_id.state == 'done'):
                if pl.production_record_id.assembly_section == u'框架':
                    frame_qty += pl.prepared_qty
                else:
                    surface_qty += pl.prepared_qty

            l.frame_completed_prep = frame_qty
            l.completed_prep = surface_qty

    @api.multi
    @api.depends('total_demand', 'completed_prep', 'frame_completed_prep')
    def _compute_incomplete_prep(self):
        for l in self:
            l.incomplete_prep = l.total_demand - l.completed_prep
            l.frame_incomplete_prep = l.total_demand - l.frame_completed_prep

    @api.multi
    @api.depends('production_record_line_ids', 'production_record_line_ids.assembling_qty')
    def _compute_assembling(self):
        for l in self:
            frame_qty = 0
            surface_qty = 0
            for pl in l.production_record_line_ids.filtered(
                    lambda x: x.production_record_id.state == 'done' and x.run_date == datetime.today().strftime(
                        "%Y-%m-%d")):
                if pl.production_record_id.assembly_section == u'框架':
                    frame_qty += pl.assembling_qty
                else:
                    surface_qty += pl.assembling_qty

            l.frame_assembling = frame_qty
            l.assembling = surface_qty

    @api.multi
    @api.depends('production_record_line_ids', 'production_record_line_ids.assembly_qty')
    def _compute_assembled(self):
        for l in self:
            frame_qty = 0
            surface_qty = 0
            for pl in l.production_record_line_ids.filtered(lambda x: x.production_record_id.state == 'done'):
                if pl.production_record_id.assembly_section == u'框架':
                    frame_qty += pl.assembly_qty
                else:
                    surface_qty += pl.assembly_qty

            l.frame_assembled = frame_qty
            l.assembled = surface_qty

    @api.multi
    @api.depends('bom_id', 'bom_id.bom_line_ids', 'bom_id.bom_line_ids.qty_assembly', 'bom_id.bom_line_ids.product_qty',
                 'bom_id.bom_line_ids.line_bom_id.bom_line_ids',
                 'bom_id.bom_line_ids.line_bom_id.bom_line_ids.qty_assembly',
                 'bom_id.bom_line_ids.line_bom_id.bom_line_ids.product_qty', 'panel_id.line_ids.qty_receive_assembly')
    def _compute_assembly_qty(self):
        for l in self:
            assembly_qty = -1
            frame_assembly_qty = -1
            for bl in l.bom_id.bom_line_ids:
                if bl.product_id.name.endswith(u' - 框架'):
                    for sbl in bl.line_bom_id.bom_line_ids:
                        frame_quantity_available = sbl.panel_line_id.qty_receive_assembly / sbl.product_qty
                        if frame_assembly_qty < 0:
                            frame_assembly_qty = frame_quantity_available
                        elif frame_assembly_qty > frame_quantity_available:
                            frame_assembly_qty = frame_quantity_available
                    l.frame_scheduled_assembly_qty = frame_assembly_qty
                else:
                    quantity_available = bl.panel_line_id.qty_receive_assembly / bl.product_qty
                    if assembly_qty < 0:
                        assembly_qty = quantity_available
                    elif assembly_qty > quantity_available:
                        assembly_qty = quantity_available
                    l.scheduled_assembly_qty = assembly_qty


    @api.multi
    @api.depends('total_demand', 'assembled', 'frame_assembled')
    def _compute_unassembled(self):
        for l in self:
            l.unassembled = l.total_demand - l.assembled
            l.frame_unassembled = l.total_demand - l.frame_assembled

    # 組合明細 Tree View Version
    @api.multi
    def act_detail(self):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'assembly_details_tree_view')[1]
        # categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        # categ = self.env['product.category'].browse(categ_id)

        return {
            'name': _("Assembly Details"),
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'mrp.bom.line',
            'domain': [('bom_id', '=', self.bom_id.id)],
            # 'res_model': 'stock.move',
            # 'domain': [('raw_material_production_id', '=', self.mo_id.id)],
            # 'res_id': self.bom_id.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
            'context': {'atlas_id': self.atlas_id.id, 'total_demand': self.total_demand},
        }

    # Calculates the percentage of completed items %
    @api.multi
    @api.depends('frame_assembled', 'frame_unassembled', 'assembled', 'unassembled', 'shipped_qty', 'undelivered_qty')
    def _compute_comp_rate(self):
        for p in self:
            if (
                    p.frame_assembled and p.frame_unassembled and p.assembled and p.unassembled and p.shipped_qty and p.undelivered_qty) > 0:
                p.frame_comp_rate = '%s%%' % round(
                    (p.frame_assembled / (p.frame_assembled + p.frame_unassembled)) * 100)
                p.complete_rate = '%s%%' % round((p.assembled / (p.assembled + p.unassembled)) * 100)
                p.shipping_comp_rate = '%s%%' % round((p.shipped_qty / (p.shipped_qty + p.undelivered_qty)) * 100)
