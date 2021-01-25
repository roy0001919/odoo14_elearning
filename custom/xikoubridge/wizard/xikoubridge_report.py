# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PrintXiKouBridgeReport(models.TransientModel):
	_name = 'xikoubridge.report'
	_description = 'Print XiKouBridge Report'

	report_date = fields.Date('Report Date')

	@api.multi
	def print_report(self):
		if not self.report_date or self.report_date == '':
			raise ValidationError(_("Please Select Target Year!!"))
		return {
			'type': 'ir.actions.act_url',
			'url': '/xikoubridge/report?d=%s&filename=report_%s.xls' % (self.report_date, self.report_date),
			'target': 'new',
		}

	# report_year = fields.Char('Year')
	# report_month = fields.Selection([
	# 	('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'), ('05', '05'), ('06', '06'),
	# 	('07', '07'), ('08', '08'), ('09', '09'), ('10', '10'), ('11', '11'), ('12', '12')
	# ], 'Month')
	#
	# @api.multi
	# def print_year(self):
	# 	if not self.report_year or self.report_year == '':
	# 		raise ValidationError(_("Please Select Target Year!!"))
	# 	return {
	# 		'type': 'ir.actions.act_url',
	# 		'url': '/biznavi_ticket/report?type=y&y=%s&m=%s&filename=report_year_%s.csv' % (self.report_year, '1', self.report_year),
	# 		'target': 'self',
	# 	}
	#
	# @api.multi
	# def print_month(self):
	# 	if not self.report_month or self.report_month == '':
	# 		raise ValidationError(_("Please Select Target Month!!"))
	# 	if not self.report_year or self.report_year == '':
	# 		raise ValidationError(_("Please Select Target Year!!"))
	#
	# 	return {
	# 		'type': 'ir.actions.act_url',
	# 		'url': '/biznavi_ticket/report?type=m&y=%s&m=%s&filename=report_month_%s_%s.csv' % (
	# 		self.report_year, self.report_month, self.report_year, self.report_month),
	# 		'target': 'self',
	# 	}
