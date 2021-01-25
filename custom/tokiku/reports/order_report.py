# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#
import logging

from odoo import api, fields, models, tools
_logger = logging.getLogger(__name__)

class OrderReport(models.Model):

    _inherit = "purchase.report"

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

