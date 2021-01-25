# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AssemblyOrderSelectWizard(models.TransientModel):
    _name = 'tokiku.assembly_po_select_wizard'
    _description = 'Select Assembly PO Item Wizard'

    tmp_grid = fields.Many2many('purchase.order.line', string='Grid')
    # partner_id = fields.Many2one('res.partner', string='Supplier')
    project_id = fields.Many2one('project.project', string='Project')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        order_id = self.env.context.get('order_id')
        panel_id = self.env.context.get('panel_id')
        panel = self.env['tokiku.panel'].browse(panel_id)
        assembly_section = self.env.context.get('assembly_section')
        order = self.env['purchase.order'].browse(order_id)
        assembly_fee = self.env['product.product'].search([('default_code', '=', 'assembly_fee'),
                                                          ('type', '=', 'service')], limit=1)

        lines = []
        for l in panel.assembly_panel_line_ids:
            if assembly_section == u'框架':
                for bl in l.bom_id.bom_line_ids.filtered(lambda x: x.product_id.name.endswith(u' - 框架')):
                    if (l.bom_id.product_id.name, l.building_id.id) not in [(p.bom_id.product_id.name, p.building_id.id) for p in order.order_line]:
                        lines.append({
                            'name': l.bom_id.product_id.name,
                            'atlas_id': l.atlas_id.id,
                            'building_id': l.building_id.id,
                            'bom_id': bl.line_bom_id.id,
                            'product_id': assembly_fee.id,
                            'product_uom': assembly_fee.uom_id.id,
                            'demand_qty': l.total_demand * bl.product_qty,
                            'date_planned': fields.Date.today(),
                            'partner_id': l.supplier_id.supplier_id.id,
                            'order_id': order_id,
                        })
            elif l.bom_id.product_id.name not in [p.bom_id.product_id.name for p in order.order_line]:
                lines.append({
                    'name': l.bom_id.product_id.name,
                    'atlas_id': l.atlas_id.id,
                    'building_id': l.building_id.id,
                    'bom_id': l.bom_id.id,
                    'product_id': assembly_fee.id,
                    'product_uom': assembly_fee.uom_id.id,
                    'demand_qty': l.total_demand,
                    'date_planned': fields.Date.today(),
                    'partner_id': l.supplier_id.supplier_id.id,
                    'order_id': order_id,
                })
        self.tmp_grid = lines

    @api.multi
    def act_select_item(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}


class PreparationSelectWizard(models.TransientModel):
    _name = 'tokiku.preparation_wizard'
    _description = 'Select Preparation Item Wizard'

    tmp_grid = fields.Many2many('tokiku.preparation_order_line', string='Grid')
    # partner_id = fields.Many2one('res.partner', string='Supplier')
    project_id = fields.Many2one('project.project', string='Project')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        panel_id = self.env.context.get('panel_id')
        panel = self.env['tokiku.panel'].browse(panel_id)
        assembly_section = self.env.context.get('assembly_section')
        preparation_id = self.env.context.get('preparation_id')
        preparation_order = self.env['tokiku.preparation_order'].browse(preparation_id)
        lines = []
        for l in panel.assembly_panel_line_ids:
            if assembly_section == u'框架':
                for bl in l.bom_id.bom_line_ids.filtered(lambda x: x.product_id.name.endswith(u' - 框架')):
                    if (bl.line_bom_id.id, l.building_id.id) not in [(p.bom_id.id, p.building_id.id) for p in preparation_order.preparation_line_ids]:
                        lines.append({
                            'assembly_panel_line_id': l.id,
                            'atlas_id': l.atlas_id.id,
                            'building_id': l.building_id.id,
                            'bom_id': bl.line_bom_id.id,
                            'demand_qty': l.total_demand * bl.product_qty,
                            'preparation_id': preparation_id,
                        })
            elif (l.bom_id.id, l.building_id.id) not in [(p.bom_id.id, p.building_id.id) for p in preparation_order.preparation_line_ids]:
                lines.append({
                    'assembly_panel_line_id': l.id,
                    'atlas_id': l.atlas_id.id,
                    'building_id': l.building_id.id,
                    'bom_id': l.bom_id.id,
                    'demand_qty': l.total_demand,
                    'preparation_id': preparation_id,
                })
        self.tmp_grid = lines

    @api.multi
    def act_select_item(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}


class AssemblySelectWizard(models.TransientModel):
    _name = 'tokiku.assembly_select_wizard'
    _description = 'Select Assembly Item Wizard'

    tmp_grid = fields.Many2many('tokiku.assembly_order_line', string='Grid')
    # partner_id = fields.Many2one('res.partner', string='Supplier')
    project_id = fields.Many2one('project.project', string='Project')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        panel_id = self.env.context.get('panel_id')
        panel = self.env['tokiku.panel'].browse(panel_id)
        assembly_section = self.env.context.get('assembly_section')
        assembly_order_id = self.env.context.get('assembly_order_id')
        assembly_order = self.env['tokiku.assembly_order'].browse(assembly_order_id)
        # panel_line_id = self.env.context.get('panel_line_id')
        lines = []
        for l in panel.assembly_panel_line_ids:
            if assembly_section == u'框架':
                for bl in l.bom_id.bom_line_ids.filtered(lambda x: x.product_id.name.endswith(u' - 框架')):
                    if (bl.line_bom_id.id, l.building_id.id) not in [(p.bom_id.id, p.building_id.id) for p in assembly_order.assembly_line_ids]:
                        lines.append({
                            'assembly_panel_line_id': l.id,
                            'atlas_id': l.atlas_id.id,
                            'building_id': l.building_id.id,
                            'bom_id': bl.line_bom_id.id,
                            'demand_qty': l.total_demand * bl.product_qty,
                            'assembly_order_id': assembly_order_id,
                            'panel_line_id': bl.panel_line_id,
                        })
            elif l.bom_id.id not in [p.bom_id.id for p in assembly_order.assembly_line_ids]:
                lines.append({
                    'assembly_panel_line_id': l.id,
                    'atlas_id': l.atlas_id.id,
                    'building_id': l.building_id.id,
                    'bom_id': l.bom_id.id,
                    'demand_qty': l.total_demand,
                    'assembly_order_id': assembly_order_id,
                    # 'panel_line_id': l.panel_line_id,
                })
        self.tmp_grid = lines

    @api.multi
    def act_select_item(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}


class ProductionRecordSelectWizard(models.TransientModel):
    _name = 'tokiku.production_wizard'
    _description = 'Select Record Item Wizard'

    tmp_grid = fields.Many2many('tokiku.production_record_line', string='Grid')
    # partner_id = fields.Many2one('res.partner', string='Supplier')
    project_id = fields.Many2one('project.project', string='Project')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        panel_id = self.env.context.get('panel_id')
        panel = self.env['tokiku.panel'].browse(panel_id)
        assembly_section = self.env.context.get('assembly_section')
        production_record_id = self.env.context.get('production_record_id')
        production_record = self.env['tokiku.production_record'].browse(production_record_id)
        lines = []
        for l in panel.assembly_panel_line_ids:
            if assembly_section == u'框架':
                for bl in l.bom_id.bom_line_ids.filtered(lambda x: x.product_id.name.endswith(u' - 框架')):
                    if (bl.line_bom_id.id, l.building_id.id) not in [(p.bom_id.id, p.building_id.id) for p in production_record.production_record_line_ids]:
                        lines.append({
                            'assembly_panel_line_id': l.id,
                            'atlas_id': l.atlas_id.id,
                            'building_id': l.building_id.id,
                            'bom_id': bl.line_bom_id.id,
                            'demand_qty': l.total_demand * bl.product_qty,
                            'production_record_id': production_record_id,
                        })
            elif l.bom_id.id not in [p.bom_id.id for p in production_record.production_record_line_ids]:
                lines.append({
                    'assembly_panel_line_id': l.id,
                    'atlas_id': l.atlas_id.id,
                    'building_id': l.building_id.id,
                    'bom_id': l.bom_id.id,
                    'demand_qty': l.total_demand,
                    'production_record_id': production_record_id,
                })
        self.tmp_grid = lines

    @api.multi
    def act_select_item(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}