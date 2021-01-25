# -*- coding: utf-8 -*-
#
from openerp import models, fields, api
from openerp.tools.safe_eval import safe_eval as eval
import time
import logging
import re

_logger = logging.getLogger(__name__)


class BiznaviResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	show_logo = fields.Boolean(string='Show company logo')
	issue_info = fields.Char(string='Invoice issue info')
	vat_img = fields.Binary(string='Invoice image')
	check_code_function = fields.Text(string='Check numbers formula')


class BiznaviAccountInvoice(models.Model):
	_name = 'account.invoice'
	_inherit = 'account.invoice'

	check_code = fields.Char(string='Check Code', compute='_compute_check_code')

	# invoiceChkCode = 0
	# o_number = TW28004668
	# for i in range(0, 8):
	#     invoiceChkCode = invoiceChkCode + ((int(o_company[i]) * int(o_number[2:][i])) % 10)
	# o_rtn = invoiceChkCode + 10
	@api.depends('number', 'company_id.vat', 'company_id.check_code_function')
	def _compute_check_code(self):
		pat = r'[A-Za-z]{2}\d{8}'
		for o in self:
			if not o.number or not re.search(pat, o.number):
				o.check_code = ''
				return

			if o.company_id.check_code_function and o.company_id.check_code_function != '':
				o.check_code = self._check_company_data(o.company_id.check_code_function, o.number)
			else:
				if o.company_id.vat and re.search(pat, o.company_id.vat):
					_logger.info('default formula for taiwan computer invoice number')
					o.check_code = self._genCheckCode(o.number, o.company_id.vat[2:])
				else:
					o.check_code = ''


	def _check_company_data(self, o_func, o_number):
		eval_context = {'o_number': o_number, 'o_rtn': 0}
		eval(o_func.strip(), eval_context, mode="exec", nocopy=True)
		return eval_context['o_rtn']

	def _taiwanDate(self, date):
		return '中華民國 %d' % (int(time.strftime('%Y', time.strptime(date, '%Y-%m-%d'))) - 1911) + time.strftime(
			' 年 %m 月 %d 日', time.strptime(date, '%Y-%m-%d'))

	def _taiwanYear(self, date):
		return "%d" % (int(time.strftime('%Y', time.strptime(date, '%Y-%m-%d'))) - 1911)

	def _currencyFmt(self, money):
		x = int(round(money, 0))
		if x < 0:
			return '-' + self._currencyFmt(x)
		result = ''
		while x >= 1000:
			x, r = divmod(x, 1000)
			result = ",%03d%s" % (r, result)
		return "%d%s" % (x, result)

	def _genCheckCode(self, o_number, o_company):
		if not o_company or len(o_company) < 8:
			return ''
		invoiceChkCode = 0
		for i in range(0, 8):
			invoiceChkCode = invoiceChkCode + ((int(o_company[i]) * int(o_number[2:][i])) % 10)
		return invoiceChkCode + 10

	def _issueInfo(self, o_company):
		if (o_company == '28004668'):
			return '本發票依台北市國稅局大安分局(稽徵所)101年7月1日(甲)字第09160866000號函核准使用。'
		else:
			return 'error'

	def _blank_line(self, nlines):
		res = []
		for i in range(nlines - self.line_no):
			res.append('')
		self.line_no = 0
		return res

	def _line_no(self, show):
		self.line_no = self.line_no + 1
		if (show):
			return self.line_no
		else:
			return ''

	def _chineseNumber(self, num):
		inputNum = str(int(round(num)))
		ar = ["零", "壹", "貳", "參", "肆", "伍", "陸", "柒", "捌", "玖"]
		cName = ["", "", "拾", "佰", "仟", "萬", "拾", "佰", "仟", "億", "拾", "佰", "仟"]
		conver = ""
		cLast = ""
		cZero = 0
		i = 1

		j = len(inputNum)

		for idx in inputNum:
			cNum = int(idx)
			cunit = cName[j]

			if cNum == 0:
				cZero = cZero + 1
				if cunit in ["萬", "億"] and cLast == '':
					cLast = cunit
			else:
				if cZero > 0:
					if conver[:len(conver)] not in ["萬", "億"]:
						conver = conver + cLast

					if cunit not in ["仟"]:
						conver = conver + "零"

					cZero = 0
					cLast = ""

				conver = conver + ar[cNum] + cunit
			j = j - 1

		if conver[:len(conver)] not in ["萬", "億"]:
			conver = conver + cLast

		return conver

# class biznavi_account_invoice(models.Model):
#     _name = 'account.invoice'
#     _inherit = 'account.invoice'
