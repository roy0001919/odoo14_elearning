# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    state = fields.Selection(selection_add=[('refund', 'Refund')])

    exp_date = fields.Char(string='Expired Date')
    pay_date = fields.Char(string='Pay Date')

    pay_no = fields.Char(string='Pay No')
    tx_no = fields.Char(string='Tx No')

    refund_date = fields.Datetime(string='Refund Date')

    refund_bank = fields.Char(string='Refund Bank')
    refund_bank_code = fields.Char(string='Refund Bank Code')
    refund_branch_code = fields.Char(string='Refund Branch Code')
    refund_name = fields.Char(string='Refund Name')
    refund_account = fields.Char(string='Refund Account')

    trace_no = fields.Char(string='Trace Number')

    partner_oauth = fields.Char(related='partner_id.user_ids.oauth_provider_id.name')
