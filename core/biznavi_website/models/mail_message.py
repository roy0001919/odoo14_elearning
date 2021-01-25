# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import _, api, fields, models, SUPERUSER_ID, tools

_logger = logging.getLogger(__name__)


class Message(models.Model):
    _inherit = 'mail.message'

    @api.multi
    def get_object_by_name(self, obj_type, obj_name):
        _logger.info('get_object call~~')
        ret_obj = self.env[obj_type].search([('name', '=', obj_name)])
        return {
            'pname': ret_obj.partner_id.name,
            'comp': ret_obj.company_id.name,
            'uom': ret_obj.amount_total,
        }
