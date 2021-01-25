# coding: utf-8

import logging
import pprint
import werkzeug
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SinopacController(http.Controller):
    _return_url = '/payment/sinopac/return'
    _cancel_url = '/payment/sinopac/cancel'
    _exception_url = '/payment/sinopac/error'
    _reject_url = '/payment/sinopac/reject'
    _inquery_url = '/payment/sinopac/inquery'

    @http.route('/payment/sinopac/inquery', type='http', auth='none', website=True, csrf=False)
    def sinopac_inquery(self, **post):
        _logger.info('sinopac_inquery with post data %s', pprint.pformat(post))  # debug

    @http.route('/payment/sinopac/back', type='http', auth='none', website=True, csrf=False)
    def sinopac_back(self, **post):
        _logger.info('sinopac_back with post data %s', pprint.pformat(post))  # debug

    @http.route([
        '/payment/sinopac/return',
        '/payment/sinopac/cancel',
        '/payment/sinopac/error',
        '/payment/sinopac/reject',
    ], type='http', auth='none', website=True, csrf=False)
    def sinopac_return(self, **post):
        """ Sinopac."""
        # _logger.info('sinopac: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        # post = dict((key, value) for key, value in post.items())
        #
        # ret_status = post.get('responseCode')  # 回應碼
        # ret_lidm = post.get('oid')  # Sale Order #
        #
        # _logger.info('sinopac Return Status: %s', ret_status)
        # parse_ret_lidm = lambda ret_lidm: ret_lidm[:ret_lidm.find('x')] if ret_lidm.find('x') != -1 else ret_lidm
        #
        # tx = request.env['payment.transaction'].sudo().search([('reference', '=', ret_lidm)])
        # order = request.env['sale.order'].sudo().search([('name', '=', parse_ret_lidm(ret_lidm))])
        # if order.state in ['cancel']:
        #     order.action_draft()
        #
        # if ret_status in ["00", "08", "11"]:
        #     request.env['payment.transaction'].sudo().form_feedback(post, 'sinopac')
        #     order.post_action()
        #     return_url = post.get('ADD_RETURNDATA') or '/shop/payment/validate?transaction_id=%s&sale_order_id=%s' % (tx.id, order.id)
        # else:
        #     order = order.copy()
        #     assert order.partner_id.id != request.website.partner_id.id
        #     Transaction = request.env['payment.transaction'].sudo()
        #     tx_values = {
        #         'acquirer_id': tx.acquirer_id.id,
        #         'type': tx.type,
        #         'amount': order.amount_total,
        #         'currency_id': order.pricelist_id.currency_id.id,
        #         'partner_id': order.partner_id.id,
        #         'partner_country_id': order.partner_id.country_id.id,
        #         'reference': Transaction.get_next_reference(order.name),
        #         'sale_order_id': order.id,
        #     }
        #
        #     tx = Transaction.create(tx_values)
        #     request.session['sale_transaction_id'] = tx.id
        #     request.session['sale_order_id'] = order.id
        #
        #     return_url = '/shop/payment?RC=%s' % ret_status
        #
        # return werkzeug.utils.redirect(return_url)

        _logger.info('sinopac: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        post = dict((key, value) for key, value in post.items())

        ret_status = post.get('status')       # 授權結果狀態
        ret_lidm = post.get('lidm')           # Sale Order #

        _logger.info('sinopac Return Status: %s', ret_status)
        parse_ret_lidm = lambda ret_lidm: ret_lidm[:ret_lidm.find('x')] if ret_lidm.find('x') != -1 else ret_lidm

        tx = request.env['payment.transaction'].sudo().search([('reference', '=', ret_lidm)])
        order = request.env['sale.order'].sudo().search([('name', '=', parse_ret_lidm(ret_lidm))])
        if order.state in ['cancel']:
            order.action_draft()

        if ret_status == "0":
            request.env['payment.transaction'].sudo().form_feedback(post, 'sinopac')
            order.post_action()
            return_url = post.get('ADD_RETURNDATA') or '/shop/payment/validate?transaction_id=%s&sale_order_id=%s' % (tx.id, order.id)
        else:
            order = order.copy()
            assert order.partner_id.id != request.website.partner_id.id
            Transaction = request.env['payment.transaction'].sudo()
            tx_values = {
                'acquirer_id': tx.acquirer_id.id,
                'type': tx.type,
                'amount': order.amount_total,
                'currency_id': order.pricelist_id.currency_id.id,
                'partner_id': order.partner_id.id,
                'partner_country_id': order.partner_id.country_id.id,
                'reference': Transaction.get_next_reference(order.name),
                'sale_order_id': order.id,
            }

            tx = Transaction.create(tx_values)
            request.session['sale_transaction_id'] = tx.id
            request.session['sale_order_id'] = order.id

            return_url = '/shop/payment?RC=%s' % ret_status

        return werkzeug.utils.redirect(return_url)
