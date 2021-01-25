# -*- coding: utf-8 -*-

from openerp import models, fields, api, SUPERUSER_ID
from datetime import datetime
import openerp
import logging

_logger = logging.getLogger(__name__)


class BiznaviHrHolidaysStatus(models.Model):
	_name = "hr.holidays.status"
	_inherit = "hr.holidays.status"
	_description = "Holiday Status"

	exp_days = fields.Integer(string='Valid Duration')


class BiznaviHrHolidaysExpired(models.Model):
	_name = "hr.holidays"
	_inherit = "hr.holidays"
	_description = "Holiday Expired"

	def run_scheduler(self, cr, uid, use_new_cursor=False, context=None):
		if context is None:
			context = {}

		try:
			if use_new_cursor:
				cr = openerp.registry(cr.dbname).cursor()

			dom = [('state', '=', 'validate'), ('type', '=', 'add')]
			ids = self.search(cr, SUPERUSER_ID, dom, context=context)
			data_holiday = self.browse(cr, uid, ids)
			x_now = datetime.now().date()
			for record in data_holiday:
				_logger.info(record.write_date)
				x_last_upd_date = datetime.strptime(record.write_date, '%Y-%m-%d %H:%M:%S').date()
				x_diff_days = (x_now - x_last_upd_date).days
				exp_days = record.holiday_status_id.exp_days
				if exp_days > 0:
					if x_diff_days > exp_days:
						record.write({'state': 'cancel', 'exp_notes': 'over %s days' % exp_days})

			if use_new_cursor:
				cr.commit()

		finally:
			if use_new_cursor:
				try:
					cr.close()
				except Exception:
					pass

		return {}
