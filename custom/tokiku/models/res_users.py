# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _get_project(self):
        return self.env.user.project_id if self.id else None

    project_id = fields.Many2one('project.project', string='Project', required=False, default=_get_project,
        help='The project this user is currently working for.', context={'user_preference': True})
    project_ids = fields.Many2many('project.project', 'res_project_users_rel', 'user_id', 'pid',
        string='Projects', default=_get_project)

    @api.model
    def _get_contract(self):
        return self.env.user.contract_id if self.id else None

    contract_id = fields.Many2one('account.analytic.contract', string='Contract', required=False, default=_get_contract,
        help='The contract this user is currently working for.', context={'user_preference': True})
    contract_ids = fields.Many2many('account.analytic.contract', 'res_contract_users_rel', 'user_id', 'contract_id',
        string='Contracts', default=_get_contract)

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights on notification_email_send
            and alias fields. Access rights are disabled by default, but allowed
            on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        init_res = super(ResUsers, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(['project_id', 'project_ids', 'contract_id', 'contract_ids'])
        # duplicate list to avoid modifying the original reference
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(['project_id', 'project_ids', 'contract_id', 'contract_ids'])
        return init_res