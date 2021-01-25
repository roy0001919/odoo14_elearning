# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PrintGangShanReport(models.TransientModel):
	_name = 'biznavi_payment_transaction.report'
	_description = 'Print Payment Transaction Report'

	report_start = fields.Date('Report Start')
	report_end = fields.Date('Report End')

	@api.multi
	def print_report(self):
		if not self.report_start or self.report_start == '' or not self.report_end or self.report_end == '':
			raise ValidationError(_("Please Select Target Month!!"))
		return {
			'type': 'ir.actions.act_url',
			'url': '/biznavi_payment_transaction/report?d=%s,%s&filename=report_%s-%s.xls' % (self.report_start, self.report_end, self.report_start, self.report_end),
			'target': 'new',
		}
