# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create_order_from_pos(self, vars):
        _logger.info('create_order_from_pos call!!')
        _logger.info('vars:%s' % vars)
        retids = []
        for var in vars:
            ret = self.env['sale.order'].create(var)
            quos = self.env['sale.order'].search([('name', '=', var['origin'])])
            for quo in quos:
                quo.ref_ticket = ret.name
            if ret:
                retids.append(var['note'])

        return retids

    @api.model
    def cancel_order_from_pos(self, vars):
        retids = []
        for var in vars:
            sol = self.env['sale.order.line'].browse(var['sol_id'])
            sol.order_id.state = 'cancel'
            retids.append(var['sol_id'])
        return retids

# @api.model
# def update_order_from_pos(self, vars):
# 	_logger.info('update_order_from_pos call!!')
# 	_logger.info('vars:%s' % vars)
# 	retids = []
# 	# for var in vars:
# 	# 	quos = self.env['sale.order'].search([('note', '=', var['note'])])
# 	# 	for quo in quos:
# 	# 		quo.state = 'cancel'
#
# 	return retids
