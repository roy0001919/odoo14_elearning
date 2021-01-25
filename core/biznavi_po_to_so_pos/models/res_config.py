# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class PosConfiguration(models.TransientModel):
    _inherit = 'pos.config.settings'

    default_pos_rest_url = fields.Char(string='Rest Url', default_model='pos.order')
    default_pos_rest_db = fields.Char(string='Rest Database', default_model='pos.order')
    default_pos_rest_usr = fields.Char(string='Rest User', default_model='pos.order')
    default_pos_rest_pwd = fields.Char(string='Rest Password', default_model='pos.order')

    @api.multi
    def set_pos_rest_values(self):
        for c in self:
            self.env['pos.config.settings'].search([('id', '!=', c.id)]).unlink()
            self.env['ir.values'].sudo().set_default(
                'pos.config.settings', 'pos_rest_url', self.default_pos_rest_url)
            self.env['ir.values'].sudo().set_default(
                'pos.config.settings', 'pos_rest_db', self.default_pos_rest_db)
            self.env['ir.values'].sudo().set_default(
                'pos.config.settings', 'pos_rest_usr', self.default_pos_rest_usr)
            self.env['ir.values'].sudo().set_default(
                'pos.config.settings', 'pos_rest_pwd', self.default_pos_rest_pwd)

