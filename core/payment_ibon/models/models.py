# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import os

_logger = logging.getLogger(__name__)


class AcquirerIbon(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('ibon', 'Ibon')])
    ibon_file_path = fields.Char('Upload Path', required_if_provider='ibon', groups='base.group_user')

    @api.model
    def _create_so_from_ibon(self):
        # _logger.info("_create_so_from_ibon call~~")
        ibon_provider = self.env['payment.acquirer'].search([('provider', '=', 'ibon')])
        # _logger.info("ibon_provider:%s" % ibon_provider)
        # _logger.info("file path:%s" % ibon_provider.ibon_file_path)
        if ibon_provider:
            d = ibon_provider.ibon_file_path
            for f in os.listdir(d):
                if not f.endswith(".done") and f.endswith(".csv"):
                    _logger.info(os.path.join(d, f))
                else:
                    _logger.info(os.path.join(d, f))