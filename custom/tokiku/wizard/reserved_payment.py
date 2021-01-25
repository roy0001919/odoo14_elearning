# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ReservedPayment(models.TransientModel):
    _name = 'reserved.payment'
    _description = 'Reserved Payment'

    project_id = fields.Many2one('project.project', string='Project')
    supplier_id = fields.Many2one('tokiku.supplier_info', string='Supplier')  # , domain=[('is_graduated', '=', True)])
    order_ids = fields.Many2many('purchase.order', string="Orders")  # compute=, domain=[('is_graduated', '=', True)])


    # @api.onchange('supplier_id')
    # def _onchange_supplier_id(self):
    #     get_project_id = self.env.context.get('project_id')
    #     get_supplier_id = self.env.context.get('supplier_info_id')
    #
    #     if get_project_id and get_supplier_id:
    #         po_list = []
    #         related_supplier_id = self.env['tokiku.supplier_info'].search([('id', '=', get_supplier_id)])
    #
    #         if related_supplier_id and len(related_supplier_id) == 1:
    #             search_pos = self.env['purchase.order'].search([()])


    @api.onchange('supplier_id')  # searching order ids depend on project_id & supplier_id
    def _onchange_supplier_id(self):
        get_project_id = self.env.context.get('project_id')
        get_supplier_id = self.env.context.get('supplier_info_id')

        if get_project_id and get_supplier_id:
            po_list = []
            related_supplier_ids = self.env['tokiku.supplier_info'].search(
                [('id', '=', get_supplier_id)])  # partner_id?
            if related_supplier_ids and len(related_supplier_ids) == 1:
                search_pos = self.env['purchase.order'].search([('project_id', '=', get_project_id), (
                'partner_id', '=', related_supplier_ids[0].supplier_ids.id)])
                # only one supplier result for this search
                for po in search_pos:
                    po_list.append(po.id)
                return {'domain': {'order_ids': [('id', 'in', po_list)]}}
        return {'domain': {'order_ids': [('id', '=', -1)]}}
        # if cannot get user_project_id & user_supplier_id then return NULL.

        # partner_id = fields.Many2one('res.partner', string='Vendor', domain="[('supplier', '=', 1)]")

        # @api.onchange('project_id')
        # def onchange_project_id(self):
        # 	supplier_ids_list = []
        # 	if self._context.get('project_id'):
        # 		supplier_info_ids = self.env["tokiku.supplier_info"].search([('project_id', '=', self._context.get('project_id'))])
        # 		for supplier_info in supplier_info_ids:
        # 			supplier_ids_list.append(supplier_info.supplier_ids)
        #
        # 	# return result['domain'] = {'supplier_id': [('id', 'in',supplier_ids_list)]}
        # 	return {'domain':{'supplier_id':[('id', 'in',supplier_ids_list)]}
