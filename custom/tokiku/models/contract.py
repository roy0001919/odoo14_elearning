# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Contract(models.Model):
    _inherit = 'account.analytic.contract'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    date_signing = fields.Date(string='Signing day')
    project_code = fields.Char(related='project_id.project_code')
    project_name = fields.Char(related='project_id.name')
    project_short_name = fields.Char(related='project_id.short_name')

    # panel_ids = fields.One2many('tokiku.panel', 'contract_id', string='Panels')
    demand_ids = fields.One2many('tokiku.demand', 'contract_id', string='Demands')
    atlas_ids = fields.One2many('tokiku.atlas', 'contract_id', string='Atlas')
    order_ids = fields.One2many('purchase.order', 'contract_id', string='Order Forms')
    # picking_wave_ids = fields.One2many('stock.picking.wave', 'contract_id', string='Picking Waves')
    picking_ids = fields.One2many('stock.picking', 'contract_id', string='Pickings')

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')

    owner_contract_number = fields.Char(string='Owner Contract Number')
    Performance_bond = fields.Integer(string='Performance Bond')
    guarantee_ticket_number = fields.Char(string='Guarantee Ticket Number')
    guarantee_ticket_delivery_date = fields.Date(string='Guarantee Ticket Delivery Date')
    guarantee_ticket_retrieval_date = fields.Date(string='Guarantee Ticket Retrieval Date')
    maintenance_bond = fields.Integer(string='Maintenance Bond')
    maintenance_ticket_number = fields.Char(string='Maintenance Ticket Number')
    maintenance_ticket_delivery_date = fields.Date(string='Maintenance Ticket Delivery Date')
    maintenance_ticket_retrieval_date = fields.Date(string='Maintenance Ticket Retrieval Date')
    remark = fields.Char(string='Remark')
    # aluminum = fields.Many2one('tokiku.panel', string='Aluminum')

    @api.multi
    def open_rec(self):
        # view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_contact_form')[1]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.analytic.contract',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            # 'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}}
        }

    @api.multi
    def open_atlas(self):
        if not self.env.user.contract_id and self.env.user.project_id:
            raise UserError(_('Please select a project and contract first!'))
            return

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_edit_form')[1]
        search_view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_tree_filter')[1]
        factories = [f.id for f in self.env.user.project_id.supplier_info_ids.filtered(lambda x: x.prod_catg.code == 'assembly')]
        # if search_view_id:
        #     print (search_view_id)
        # panel_id = self.env['tokiku.panel'].search([('contract_id', '=', self.id), ('type', '=', 'Aluminum')]).id
        return {
            'name': _('Processing Atlas'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'tokiku.atlas',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_view_id,
            # 'res_id': panel_id,
            'type': 'ir.actions.act_window',
            # 'view_id': tree_id,
            'target': 'current',
            # 'flags': {'form': {'action_buttons': True}},
            # 'key2': 'client_action_multi',
            'domain': [('contract_id.project_id', '=', self.env.user.project_id.id),
                       # ('contract_id', '=', self.env.user.contract_id.id),
                       ('atlas_version', '=', 0),
                       ],
            'context': {'default_contract_id': self.env.user.contract_id.id,
                        'factories': factories,
                        # 'search_default_name': 1,
                        }
        }

    def open_not_purchase_table(self):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_not_purchase_table')[1]

        not_purchase_table = self.env['tokiku.panel_line'].sudo().search([('panel_id.project_id', '=', self.env.user.project_id.id),
                                                                          ('rest_demand_qty', '>', 0)])
        return {
            'name': _('Panel Not Purchase Table'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.panel',
            # 'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            # 'context': {'default_categ_id': categ.id, 'default_contract_id': self.id}
        }
