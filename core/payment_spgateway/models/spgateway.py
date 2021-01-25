# -*- coding: utf-8 -*-
import hashlib
import json
import urlparse
import util
import urllib
from openerp import models, fields, api
import time
import logging
import werkzeug.urls

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from core.payment_spgateway.controllers.main import SpgatewayController

_logger = logging.getLogger(__name__)


class AcquirerSpgateway(models.Model):
	_inherit = 'payment.acquirer'

	provider = fields.Selection(selection_add=[('spgateway', 'Spgateway')])
	sp_merchant_id = fields.Char('Spgateway Merchant ID', required_if_provider='spgateway')
	sp_hash_key = fields.Char('Spgateway Hash Key', required_if_provider='spgateway')
	sp_hash_iv = fields.Char('Spgateway Hash IV', required_if_provider='spgateway')

	def _get_spgateway_url(self, environment):
		if environment == 'prod':
			return {
				'spgateway_url': 'https://core.spgateway.com/MPG/mpg_gateway'
			}
		else:
			return {
				'spgateway_url': 'https://ccore.spgateway.com/MPG/mpg_gateway'
			}

	# @api.model
	# def _get_providers(self):
	# 	providers = super(AcquirerSpgateway, self)._get_providers()
	# 	providers.append(['spgateway', 'spgateway'])
	# 	return providers

	@api.multi
	def spgateway_get_form_action_url(self):
		self.ensure_one()
		return self._get_spgateway_url(self.environment)['spgateway_url']

	@api.multi
	def spgateway_form_generate_values(self, values):
		self.ensure_one()
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		date_create = int(time.time())
		merchant_id = getattr(self, 'sp_merchant_id')
		sp_hash_key = getattr(self, 'sp_hash_key')
		sp_hash_iv = getattr(self, 'sp_hash_iv')
		amount = int(round(values['amount']))
		spgateway_tx_values = dict(values)
		spgateway_tx_values.update({
			'MerchantID': merchant_id,
			'RespondType': 'JSON',
			'TimeStamp': date_create,
			'Version': '1.2',
			'MerchantOrderNo': values['reference'],
			'Amt': amount,
			'ItemDesc': self.company_id.name,
			'Email': values['partner_email'],
			'LoginType': '0',
			'ReturnURL': '%s' % urlparse.urljoin(base_url, SpgatewayController._return_url),
			'NotifyURL': '%s' % urlparse.urljoin(base_url, SpgatewayController._notify_url),
		})

		to_sign = {}
		to_sign.update({
			'Amt': amount,
			'MerchantID': merchant_id,
			'MerchantOrderNo': values['reference'],
			'TimeStamp': date_create,
			'Version': '1.2',
		})

		# sorted_to_sign = sorted(to_sign.iteritems())
		# url_encode_str = urllib.urlencode(sorted_to_sign)
		# final_str = 'HashKey=%s&%s&HashIV=%s' % (sp_hash_key, url_encode_str, sp_hash_iv)
		# hash_str = hashlib.sha256(final_str).hexdigest().upper()

		sorted_to_sign = sorted(to_sign.iteritems())
		sorted_to_sign.insert(0, ('HashKey', sp_hash_key))
		sorted_to_sign.append(('HashIV', sp_hash_iv))
		string_to_sign = util.do_str_replace(urllib.quote(werkzeug.url_encode(sorted_to_sign), '+&'))

		spgateway_tx_values['CheckValue'] = hashlib.sha256(string_to_sign).hexdigest().upper()

		return spgateway_tx_values


class TxSpgateway(models.Model):
	_inherit = 'payment.transaction'

	spgateway_txn_id = fields.Char('Transaction ID')
	spgateway_txn_type = fields.Char('Transaction type')

	# --------------------------------------------------
	# FORM RELATED METHODS
	# --------------------------------------------------
	@api.model
	def _spgateway_form_get_tx_from_data(self, data):
		result = json.loads(data).get('Result')
		result_dict = json.loads(result)
		reference, txn_id = result_dict.get('MerchantOrderNo'), result_dict.get('TradeNo')
		if not reference or not txn_id:
			error_msg = 'Spgateway: received data with missing reference (%s) or txn_id (%s)' % (reference, txn_id)
			_logger.error(error_msg)
			raise ValidationError(error_msg)

		# find tx -> @TDENOTE use txn_id ?
		payment_tx = self.search([('reference', '=', reference)])
		if not payment_tx or len(payment_tx) > 1:
			error_msg = 'Spgateway: received data for reference %s' % (reference)
			if not payment_tx:
				error_msg += '; no order found'
			else:
				error_msg += '; multiple order found'
			_logger.error(error_msg)
			raise ValidationError(error_msg)
		return payment_tx
		# tx = self.browse(cr, uid, tx_ids[0], context=context)
		# acquirer = tx.acquirer_id
		# _logger.info('acquirer id: %s' % acquirer.id)
		# CheckValue_result = self.pool['payment.acquirer'].checkout_feedback(cr, uid, acquirer.id, data, context=context)
		# if CheckValue_result:
		# 	return tx
		#
		# else:
		# 	error_msg = 'Spgateway: invalid CheckValue, received %s, computed %s' % (data.get('CheckValue'), CheckValue_result)
		# 	_logger.warning(error_msg)
		# 	raise ValidationError(error_msg)

	@api.model
	def _spgateway_form_validate(self, tx, data):
		JSONData = json.loads(data)
		status = JSONData.get('Status')
		_message = JSONData.get('Message')
		result = json.loads(JSONData.get('Result'))
		data = {
			'acquirer_reference': result.get('MerchantOrderNo'),
			'spgateway_txn_id': result.get('TradeNo'),
			'spgateway_txn_type': result.get('PaymentType'),
		}

		if status == 'SUCCESS':
			_logger.info('Validated Spgateway payment for tx %s: set as done' % (tx.reference))
			data.update(state='done', date_validate=data.get('PaymentDate', fields.datetime.now()), state_message=_message)
			return tx.write(data)
		else:
			error = 'Received unrecognized status for Spgateway payment %s: %s, set as error' % (tx.reference, status)
			_logger.info(error)
			data.update(state='error', state_message=error)
			return tx.write(data)

