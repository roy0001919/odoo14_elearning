# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import logging
import pprint
import urllib2
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class allPayController(http.Controller):
    _return_url = '/payment/allpay/return/'
    _order_result_url = '/payment/allpay/orderresult'

    @http.route('/payment/allpay/return', type='http', auth="none", methods=['POST', 'GET'], csrf=False)
    def allpay_return(self, **post):
        _logger.info('Beginning Allpay form_feedback with post data %s', pprint.pformat(post))  # debug
        if post.get('RtnCode') in ['1', '800']:
            request.registry['payment.transaction'].form_feedback(request.cr, SUPERUSER_ID, post, 'allpay', context=request.context)

    @http.route('/payment/allpay/orderresult', type='http', auth="none", csrf=False)
    def allpay_orderresult(self, **post):
        _logger.info('Call by Allpay........%s' % post)
        request.registry['payment.transaction'].form_feedback(request.cr, SUPERUSER_ID, post, 'allpay', context=request.context)

        return werkzeug.utils.redirect('/shop/payment/validate')
