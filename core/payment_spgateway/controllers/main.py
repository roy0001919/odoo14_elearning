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


class SpgatewayController(http.Controller):
	_return_url = '/payment/spgateway/return/'
	_notify_url = '/payment/spgateway/notify'

	@http.route('/payment/spgateway/notify', type='http', auth="none", methods=['POST', 'GET'], csrf=False)
	def spgateway_return(self, **post):
		_logger.info('Beginning spgateway form_feedback with post data %s', pprint.pformat(post))  # debug
		data = post.get('JSONData')
		status = json.loads(data).get('Status')
		if status == 'SUCCESS':
			request.env['payment.transaction'].sudo().form_feedback(data, 'spgateway')

	@http.route('/payment/spgateway/return', type='http', auth="none", csrf=False)
	def spgateway_orderresult(self, **post):
		_logger.info('Call by Spgateway........%s' % post)
		request.env['payment.transaction'].sudo().form_feedback(post.get('JSONData'), 'spgateway')

		return werkzeug.utils.redirect('/shop/payment/validate')
