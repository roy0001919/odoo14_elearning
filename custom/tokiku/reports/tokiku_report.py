# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class PreparationOrderReport(models.AbstractModel):
    _name = 'report.tokiku.report_preparation_order'

    @api.model
    def get_lines(self, obj):
        data = []
        for pl in obj.preparation_line_ids:
            tmp_name = pl.bom_id.product_tmpl_id.display_name or ""
            tmp_building = pl.building_id.name or ""
            tmp_atlas_id = pl.atlas_id.name or ""
            tmp_demand_qty = pl.demand_qty or ""
            tmpObj = {
                'name': tmp_name,
                'building': tmp_building,
                'demand_qty': tmp_demand_qty,
                'atlas_id': tmp_atlas_id,
            }
            data.append(tmpObj)

        return data

    @api.multi
    def render_html(self, docids, data=None):
        docids = docids or self._context.get('active_ids')
        _logger.info('docids: %s' % docids)
        po = self.env['tokiku.preparation_order'].browse(docids)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'tokiku.preparation_order',
            'get_lines': self.get_lines,
            'docs': po,
        }
        return self.env['report'].render('tokiku.report_preparation_order', docargs)


class AssemblyOrderReport(models.AbstractModel):
    _name = 'report.tokiku.report_assembly_order'

    @api.model
    def get_lines(self, obj):
        data = []
        for pl in obj.assembly_line_ids:
            tmp_name = pl.bom_id.product_tmpl_id.display_name or ""
            tmp_building = pl.building_id.name or ""
            tmp_atlas_id = pl.atlas_id.name or ""
            tmp_demand_qty = pl.assembly_qty or ""
            tmpObj = {
                'name': tmp_name,
                'building': tmp_building,
                'demand_qty': tmp_demand_qty,
                'atlas_id': tmp_atlas_id,
            }
            data.append(tmpObj)

        return data

    @api.multi
    def render_html(self, docids, data=None):
        docids = docids or self._context.get('active_ids')
        _logger.info('docids: %s' % docids)
        po = self.env['tokiku.assembly_order'].browse(docids)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'tokiku.assembly_order',
            'get_lines': self.get_lines,
            'docs': po,
        }
        return self.env['report'].render('tokiku.report_assembly_order', docargs)
