# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class ProductionRecordSelectWizard(models.TransientModel):
    _name = 'tokiku.inst_production_wizard'
    _description = 'Select Record Item Wizard'

    tmp_grid = fields.Many2many('tokiku.inst_prodrec_line', string='Grid')
    # partner_id = fields.Many2one('res.partner', string='Supplier')
    project_id = fields.Many2one('project.project', string='Project')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        panel_id = self.env.context.get('panel_id')
        panel = self.env['tokiku.panel'].browse(panel_id)
        inst_production_record_id = self.env.context.get('inst_prodrec_id')
        product_record_line = self.env['tokiku.inst_prodrec'].browse(inst_production_record_id)
        lines = []
        exist_lines_product = [l.product_id.id for l in product_record_line.inst_prodrec_ids]
        for line in panel.installation_panel_line_ids:
            if line.feed_total_qty > 0 and line.installed_qty == 0:
                lines.append(({'atlas_name': line.atlas_name,
                               'installation_panel_line_id': line.id,
                               'product_id': line.product_id.id,
                               'building_id': line.building_id.id,
                               'floor': line.floor,
                               'install_categ': line.install_categ_id.id,
                               'product_categ': line.product_categ,
                               'install_loc': line.install_loc_id.id,
                               'default_code': line.default_code,
                               'demand_qty': line.demand_qty,
                               'order_qty': line.order_qty,
                               'feed_total_qty': line.feed_total_qty,
                               'installed_qty': line.feed_total_qty,
                               'installed_surface': line.installed_surface,
                               'inst_prodrec_id': inst_production_record_id,
                               }))
        lines_n = list(filter(lambda x: x['product_id'] not in exist_lines_product, lines))
        self.tmp_grid = lines_n

    @api.multi
    def act_select_item(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}