# -*- coding: utf-8 -*-
import json

from odoo import models
from odoo.http import request

import odoo


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(Http, self).session_info()
        user = request.env.user
        project_ids = request.env['project.project'].search([('active', '=', True)])
        result['project_id'] = user.project_id.id if user.project_id else None if request.session.uid else None
        result['user_projects'] = {'current_project': (user.project_id.id, user.project_id.short_name),
                           'allowed_projects': [(p.id, p.short_name) for p in project_ids]}

        if user.project_id:
            contract_ids = user.project_id.contract_ids
            if user.contract_id.id not in [c.id for c in contract_ids]:
                user.contract_id = user.project_id.contract_id if user.project_id.contract_id else contract_ids[0] if len(contract_ids) > 0 else None
            user.project_id.contract_id = user.contract_id
            result['contract_id'] = user.contract_id.id if request.session.uid else None
            result['user_contracts'] = {'current_contract': (user.contract_id.id, user.contract_id.name),
                               'allowed_contracts': [(c.id, c.name) for c in contract_ids]}
        return result

