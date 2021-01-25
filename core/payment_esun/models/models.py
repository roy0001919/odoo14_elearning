# coding: utf-8

import base64
import json
import binascii
from collections import OrderedDict
import hashlib
import hmac
import logging
import urlparse
from hashlib import sha256
import json
import datetime, pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from core.payment_esun.controllers.controllers import EsunController

_logger = logging.getLogger(__name__)


class AcquirerEsun(models.Model):
	_inherit = 'payment.acquirer'

	provider = fields.Selection(selection_add=[('esun', 'Esun')])
	esun_merchant_account = fields.Char('Merchant Account', required_if_provider='esun', groups='base.group_user')
	esun_code = fields.Char('Code', required_if_provider='esun', groups='base.group_user')
	esun_mac_key = fields.Char('MAC Key', required_if_provider='esun', groups='base.group_user')

	def _get_feature_support(self):
		"""Get advanced feature support by provider.

		Each provider should add its technical in the corresponding
		key for the following features:
			* fees: support payment fees computations
			* authorize: support authorizing payment (separates
						 authorization and capture)
			* tokenize: support saving payment data in a payment.tokenize
						object
		"""
		res = super(AcquirerEsun, self)._get_feature_support()
		res['authorize'].append('esun')
		return res

	@api.model
	def _get_esun_urls(self, environment):
		if environment == 'test':
			return {
				'esun_61_url': 'https://acqtest.esunbank.com.tw/ACQTrans/online/sale61.htm',
				'esun_014_url': 'https://acqtest.esunbank.com.tw/ACQTrans/esuncard/txnf014s',
				'esun_015_url': 'https://acqtest.esunbank.com.tw/ACQTrans/esuncard/txnf0150',
				'esun_016_url': 'https://acqtest.esunbank.com.tw/ACQTrans/esuncard/txnf0160',
				'esun_018_url': 'https://acqtest.esunbank.com.tw/ACQQuery/esuncard/txnf0180'
			}
		else:
			return {
				'esun_61_url': 'https://acq.esunbank.com.tw/acq_online/online/sale61.htm',
				'esun_014_url': 'https://acq.esunbank.com.tw/ACQTrans/esuncard/txnf014s',
				'esun_015_url': 'https://acq.esunbank.com.tw/ACQTrans/esuncard/txnf0150',
				'esun_016_url': 'https://acq.esunbank.com.tw/ACQTrans/esuncard/txnf0160',
				'esun_018_url': 'https://acq.esunbank.com.tw/ACQQuery/esuncard/txnf0180'
			}

	@api.multi
	def _esun_generate_merchant_sig_sha256(self, inout, values):
		def escapeVal(val):
			return val.replace('\\', '\\\\').replace(':', '\\:')

		assert inout in ('in', 'out')
		assert self.provider == 'esun'

		if inout == 'in':
			keys = [
				'ONO', 'U', 'MID', 'BPF', 'IC', 'TA', 'TID',
			]
		else:
			keys = [
				'RC', 'MID', 'ONO', 'LTD', 'LTT', 'RRN', 'AIR', 'AN',
				'ITA', 'IP', 'IPA', 'IFPA',
				'BB', 'BRP', 'BRA',
			]

		mac_key = self.esun_mac_key
		raw_values = OrderedDict()
		for k in keys:
			if k in values:
				raw_values[k] = values[k]
		data = '%s%s' % (json.dumps(raw_values).replace(' ', ''), mac_key)
		print('data: %s' % data)
		shasign = sha256(data).hexdigest()
		print('shasign: %s' % shasign)
		return shasign

	@api.multi
	def _esun_generate_merchant_sig(self, inout, values):
		_logger.info('_esun_generate_merchant_sig: %s' % values)
		assert inout in ('in', 'out')
		assert self.provider == 'esun'

		if inout == 'in':
			keys = "MID CID ONO TA TT U TXNNO M".split()
		else:
			keys = "RC MID ONO LTD LTT TRACENUMBER TRACETIME TXNNO".split()

		def get_value(key):
			if values.get(key):
				return values[key]
			return ''

		# {'MID': '8080000002', 'CID': '', 'ONO': '1335786620125', 'TA': '100', 'TT': '01', 'U': '/TestACQ/print.html', 'TXNNO': '', 'M': '13HYMXS6BENMU921SELBNGQMUMH4RGBE'}
		sign = '&'.join('%s' % get_value(k) for k in keys).encode('ascii')
		if inout == 'out':
			sign = '%s&%s' % (sign, self.esun_mac_key)
		# 15d0ac90c0c7bc40b4701508cf6cc0b9
		return hashlib.md5(sign).hexdigest()

	def get_sort_dict(self, values):
		keys = [
			'ONO', 'U', 'MID', 'BPF', 'IC', 'TA', 'TID',
		]
		raw_values = OrderedDict()
		for k in keys:
			if k in values:
				raw_values[k] = values[k]

		data = '%s' % (json.dumps(raw_values).replace(' ', ''))
		return data

	@api.multi
	def esun_form_generate_values(self, values):
		_logger.info('esun_form_generate_values: %s' % values)
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		values.update({
			'ONO': values['reference'],
			'U': '%s' % urlparse.urljoin(base_url, EsunController._return_url),
			'MID': self.esun_code,
			'TA': '%d' % int(tools.float_round(values['amount'], 2)),
			'TID': 'EC000001',
		})

		mac = self._esun_generate_merchant_sig_sha256('in', values)

		post_val = {}
		post_val.update({
			'data': self.get_sort_dict(values),
			'mac': mac,
			'ksn': 1,
		})
		return post_val

	@api.multi
	def esun_get_form_action_url(self):
		return self._get_esun_urls(self.environment)['esun_014_url']


	# 取消授權背端
	@api.multi
	def esun_get_form_action_cancel_url(self):
		return self._get_esun_urls(self.environment)['esun_015_url']

	@api.multi
	def _esun_generate_merchant_sig_cancel_sha256(self, inout, values):
		def escapeVal(val):
			return val.replace('\\', '\\\\').replace(':', '\\:')

		assert inout in ('in', 'out')
		assert self.provider == 'esun'

		if inout == 'in':
			keys = [
				'ONO', 'MID',
			]
		else:
			keys = [
				'RC', 'MID', 'ONO', 'LTD', 'LTT', 'RRN', 'AIR',
			]

		mac_key = self.esun_mac_key
		raw_values = OrderedDict()
		for k in keys:
			if k in values:
				raw_values[k] = values[k]

		_logger.info('raw_values: %s' % raw_values)
		data = '%s%s' % (json.dumps(raw_values).replace(' ', ''), mac_key)
		_logger.info('raw_data: %s' % data)
		shasign = sha256(data).hexdigest()
		# print('shasign: %s' % shasign)
		return shasign

	@api.multi
	def esun_form_cancel_generate_values(self, values):
		_logger.info('esun_form_cancel_generate_values: %s' % values)
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		values.update({
			'ONO': values['reference'],
			'MID': self.esun_code,
		})

		mac = self._esun_generate_merchant_sig_cancel_sha256('in', values)

		post_val = {}
		post_val.update({
			'data': self.get_sort_dict(values),
			'mac': mac,
			'ksn': 1,
		})
		_logger.info("post_val: %s" % post_val);
		return post_val


class TxEsun(models.Model):
	_inherit = 'payment.transaction'

	# --------------------------------------------------
	# FORM RELATED METHODS
	# --------------------------------------------------

	@api.model
	def _esun_form_get_tx_from_data(self, data):
		_logger.info('_esun_form_get_tx_from_data: %s' % data)
		resp = data.get('DATA')
		if not resp:
			resp = data.get('RC')
			respArr = resp.split(',')
			resCode, reference = respArr[0], respArr[2].split('=')[1]
		else:
			respArr = resp.split(',')
			resp_dict = {}
			for respArrObj in respArr:
				respObj = respArrObj.split('=')
				resp_dict[respObj[0]] = respObj[1]
			resCode, reference = resp_dict.get('RC'), resp_dict.get('ONO')
		if resCode != "00":
			error_msg = _('Esun: received data with missing reference (%s) or Response Code (%s)') % (reference, resCode)
			_logger.info(error_msg)
			raise ValidationError(error_msg)

		tx = self.env['payment.transaction'].search([('reference', '=', reference)])
		if not tx or len(tx) > 1:
			error_msg = _('Esun: received data for reference %s') % (reference)
			if not tx:
				error_msg += _('; no order found')
			else:
				error_msg += _('; multiple order found')
			_logger.info(error_msg)
			raise ValidationError(error_msg)

		_logger.info('_esun_form_get_tx_from_data (tx): %s' % tx)
		# # verify shasign
		# shasign_check = tx.acquirer_id._esun_generate_merchant_sig('out', data)
		#
		# if shasign_check != data.get('M'):
		# 	error_msg = _('Esun: invalid merchantSig, received %s, computed %s') % (data.get('M'), shasign_check)
		# 	_logger.warning(error_msg)
		# 	raise ValidationError(error_msg)

		return tx

	def _esun_form_get_invalid_parameters(self, data):
		_logger.info('_esun_form_get_invalid_parameters: %s' % data)
		invalid_parameters = []
		resp = data.get('DATA')
		if not resp:
			resp = data.get('RC')
			respArr = resp.split(',')
			resCode, reference = respArr[0], respArr[2].split('=')[1]
		else:
			respArr = resp.split(',')
			resp_dict = {}
			for respArrObj in respArr:
				respObj = respArrObj.split('=')
				resp_dict[respObj[0]] = respObj[1]
			resCode, reference = resp_dict.get('RC'), resp_dict.get('ONO')

		# sale_order number
		if self.acquirer_reference and reference != self.acquirer_reference:
			invalid_parameters.append(('Reference', reference, self.acquirer_reference))
		# Response Code
		if resCode not in ['00']:
			invalid_parameters.append(('Result', resCode, 'Transaction Fail.'))

		return invalid_parameters

	def _esun_form_validate(self, data):
		_logger.info('_esun_form_validate: %s' % data)
		resp = data.get('DATA')
		respArr = resp.split(',')
		resp_dict = {}
		for respArrObj in respArr:
			respObj = respArrObj.split('=')
			resp_dict[respObj[0]] = respObj[1]

		status = resp_dict.get('RC')
		if status == '00':
			self.write({
				'state': 'authorized',
				'acquirer_reference': resp_dict.get('ONO'),
			})
			return True
		elif status == 'PC  ':
			self.write({
				'state': 'pending',
				'acquirer_reference': resp_dict.get('ONO'),
			})
			return True
		else:
			error = _('Esun: feedback error')
			_logger.info(error)
			self.write({
				'state': 'error',
				'state_message': error
			})
			return False

	# 取消授權背端
	@api.model
	def _esun_form_cancel_get_tx_from_data(self, data):
		_logger.info('_esun_form_cancel_get_tx_from_data: %s' % data)
		resp = data.get('DATA')
		resCode = resp.get('returnCode')
		txnData = resp.get('txnData')

		reference = txnData.get('ONO')
		if resCode != "00":
			error_msg = _('Esun: received data with missing reference (%s) or Response Code (%s)') % (
			reference, resCode)
			_logger.info(error_msg)
			raise ValidationError(error_msg)

		tx = self.env['payment.transaction'].search([('reference', '=', reference)])
		if not tx or len(tx) > 1:
			error_msg = _('Esun: received data for reference %s') % (reference)
			if not tx:
				error_msg += _('; no order found')
			else:
				error_msg += _('; multiple order found')
			_logger.info(error_msg)
			raise ValidationError(error_msg)

		_logger.info('_esun_form_get_tx_from_data (tx): %s' % tx)
		# # verify shasign
		# shasign_check = tx.acquirer_id._esun_generate_merchant_sig('out', data)
		#
		# if shasign_check != data.get('M'):
		# 	error_msg = _('Esun: invalid merchantSig, received %s, computed %s') % (data.get('M'), shasign_check)
		# 	_logger.warning(error_msg)
		# 	raise ValidationError(error_msg)

		return tx

	@api.multi
	def esun_s2s_capture_transaction(self, **kwargs):
		for tx in self:
			tx.state = 'done'

	@api.model
	def _capture_transaction_lastmonth(self, year_month=None):
		tz = pytz.timezone(self.env.context.get('tz') or 'UTC')
		if year_month:
			d = tz.localize(datetime.datetime.strptime(year_month, "%Y-%m")).astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
		else:
			d = tz.localize(datetime.datetime.utcnow().replace(day=1,hour=0,minute=0,second=0)).astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
		ptxs = self.env['payment.transaction'].search([('create_date', '<', d),('state', '=', 'authorized')])
		for ptx in ptxs:
			ptx.state = 'done'
