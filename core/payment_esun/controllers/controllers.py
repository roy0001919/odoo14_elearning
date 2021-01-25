# coding: utf-8

import logging
import pprint
import werkzeug
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class EsunController(http.Controller):
    _return_url = '/payment/esun/return'
    _cancel_url = '/payment/esun/cancel'
    _exception_url = '/payment/esun/error'
    _reject_url = '/payment/esun/reject'

    @http.route([
        '/payment/esun/return',
        '/payment/esun/cancel',
        '/payment/esun/error',
        '/payment/esun/reject',
    ], type='http', auth='none', website=True, csrf=False)
    
    def esun_return(self, **post):
        """ Esun."""
        _logger.info('eEun: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        post = dict((key.upper(), value) for key, value in post.items())
        resp = post.get('DATA')
        if not resp:
            resp = post.get('RC')
            respArr = resp.split(',')
            resCode, reference = respArr[0], respArr[2].split('=')[1]
        else:
            respArr = resp.split(',')
            resp_dict = {}
            for respArrObj in respArr:
                respObj = respArrObj.split('=')
                resp_dict[respObj[0]] = respObj[1]
            resCode, reference = resp_dict.get('RC'), resp_dict.get('ONO')
        _logger.info('eEun resCode: %s', resCode)
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        order = request.env['sale.order'].sudo().search([('name', '=', reference)])
        if order.state in ['cancel']:
            order.action_draft()
        if resCode == "00":
            request.env['payment.transaction'].sudo().form_feedback(post, 'esun')
            order.post_action()
            # request.session['sale_order_id'] = order.id
            return_url = post.get('ADD_RETURNDATA') or '/shop/payment/validate?transaction_id=%s&sale_order_id=%s' % (tx.id, order.id)
        else:
            # tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
            # order = request.website.sale_get_order(force_create=1)
            # request.session['sale_order_id'] = order.id
            # order.name = request.env['ir.sequence'].sudo().next_by_code('sale.order') or 'New'
            # order = order.copy()
            # tx.reference = order.name
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
            # if token and request.env['payment.token'].sudo().browse(int(token)).partner_id == order.partner_id:
            #     tx_values['payment_token_id'] = token

            tx = Transaction.create(tx_values)
            # tx.reference = order.name
            # tx.sale_order_id = order.id
            request.session['sale_transaction_id'] = tx.id
            request.session['sale_order_id'] = order.id

            return_url = '/shop/payment?RC=%s' % resCode
        # else:
            # tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
            # if order.state in ['draft', 'cancel']:
                # order.action_draft()
                # order.name = request.env['ir.sequence'].sudo().next_by_code('sale.order') or 'New'
                # tx.reference = order.name
            #     order = order.copy()
            #     tx.reference = order.name
            #     return_url = '/shop/payment?RC=%s' % resCode
            # else:
            #     request.website.sale_reset()
            #     return_url = '/my/orders'

        return werkzeug.utils.redirect(return_url)
