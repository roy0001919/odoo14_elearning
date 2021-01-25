# -*- coding: utf-8 -*-

from openerp.osv import osv
import logging

_logger = logging.getLogger(__name__)

_ret_vat = {
	'tw': 'TW12345679'
}

_tw_tax_rule = [1,2,1,2,1,2,4,1]


class ResPartner(osv.osv):
	_inherit = 'res.partner'

	def _cc(self, n):
		x = n
		if n > 9:
			x1 = n % 10
			x2 = (n/10)%10
			x = x1 + x2

		return x

	def _chk_vat_num(self, vat):
		sum_vat = 0
		vat_no = str(vat)

		for i in range(0,8):
			sum_vat += self._cc(int(vat_no[i]) * _tw_tax_rule[i])

		if sum_vat % 10 == 0:
			return True
		elif (vat_no[6] == "7") and ((sum_vat+1) % 10 == 0):
			return True

		return False

	def check_vat_tw(self, vat):
		_logger.info('VAT Number [%s]' % vat)
		if len(vat) != 8:
			return False
		try:
			int(vat)
		except ValueError:
			return False

		_logger.info('flag1')
		if self._chk_vat_num(vat):
			_logger.info('flag2')
			return True

		return False
