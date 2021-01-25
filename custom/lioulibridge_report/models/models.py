# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DDF
from datetime import datetime
import pytz
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	p_date = fields.Char('Date for Print', compute='_compute_p_date', store=True)
	order_user = fields.Char(related='partner_id.name')
	order_num = fields.Char(related='order_id.name')

	@api.depends('booking_start')
	def _compute_p_date(self):
		tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
		for rec in self:
			if rec.booking_start:
				rec.p_date = datetime.strftime(datetime.strptime(rec.booking_start, DTF).replace(tzinfo=pytz.utc).astimezone(tz), DDF)
#
#
# class SaleOrder(models.Model):
# 	_inherit = 'sale.order'
#
# 	p_year = fields.Char('Year for print', compute='_compute_p_year', store=True)
# 	p_month = fields.Char('Month for print', compute='_compute_p_month', store=True)
#
# 	@api.depends('date_order')
# 	def _compute_p_year(self):
# 		tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
# 		for rec in self:
# 			rec.p_year = datetime.strftime(datetime.strptime(rec.date_order, DTF).replace(tzinfo=pytz.utc).astimezone(tz), '%Y')
#
# 	@api.depends('date_order')
# 	def _compute_p_month(self):
# 		tz = pytz.timezone(self.sudo().env['res.users'].browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
# 		for rec in self:
# 			rec.p_month = datetime.strftime(datetime.strptime(rec.date_order, DTF).replace(tzinfo=pytz.utc).astimezone(tz), '%m')
