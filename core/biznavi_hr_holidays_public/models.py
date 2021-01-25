# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools
from openerp.exceptions import except_orm, Warning
from datetime import date, datetime
from datetime import timedelta
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class HrHolidaysPublic(models.Model):
	_name = 'hr.holidays.public'
	_description = "Public Holidays"

	year = fields.Char(string='Calendar Year', required=True)
	line_ids = fields.One2many(comodel_name='hr.holidays.public.line', inverse_name='holidays_id', string='Holiday Dates')

	_translate = True
	_rec_name = 'year'
	_order = "year"
	_sql_constraints = [
		('year_unique', 'UNIQUE(year)', _('Duplicate year!')),
	]

	def is_public_holiday(self, cr, uid, dt, context=None):

		ph_obj = self.pool.get('hr.holidays.public')
		ph_ids = ph_obj.search(cr, uid, [('year', '=', dt.year), ], context=context)
		if len(ph_ids) == 0:
			return False

		for line in ph_obj.browse(cr, uid, ph_ids[0], context=context).line_ids:
			if date.strftime(dt, "%Y-%m-%d") == line.date:
				# _logger.info("bingo: %s" % line.date)
				return True

		return False

	def get_holidays_list(self, cr, uid, year, context=None):

		res = []
		ph_ids = self.search(cr, uid, [('year', '=', year)], context=context)
		if len(ph_ids) == 0:
			return res
		[res.append(l.date) for l in self.browse(cr, uid, ph_ids[0], context=context).line_ids]

		return res


class hr_holidays_public_line(models.Model):
	_name = 'hr.holidays.public.line'

	name = fields.Char(string='Name', size=128, required=True)
	date = fields.Date(string='Date', required=True)
	holidays_id = fields.Many2one(comodel_name='hr.holidays.public', string='Holiday Calendar Year', ondelete='cascade')
	variable = fields.Boolean(string='Date may change')
	adj_working_day = fields.Boolean(string='Adjusted Working Day')

	_order = 'date, name desc'
	_translate = True


# class hr_holidays(models.Model):
# 	_name = "hr.holidays"
# 	_inherit = "hr.holidays"
#
# 	def create(self, cr, uid, values, context=None):
# 		if context is None:
# 			context = {}
# 		context = dict(context, mail_create_nolog=True)
#
# 		if values['type'] == 'remove':
# 			_logger.info("get from / to date: %s, %s" % (values['date_from'], values['date_to']))
#
# 			x_days_tmp = values['number_of_days_temp']
# 			x_date_from = datetime.strptime(values['date_from'], tools.DEFAULT_SERVER_DATETIME_FORMAT)
# 			x_date_to = datetime.strptime(values['date_to'], tools.DEFAULT_SERVER_DATETIME_FORMAT)
# 			x_diff_days = (x_date_to - x_date_from).days
#
# 			_logger.info("temp days: %s" % x_days_tmp)
# 			_logger.info("diff days: %s" % x_diff_days)
#
# 			obj_pub_holidays = self.pool.get('hr.holidays.public')
# 			cnt_conflict_days = 0
# 			for chk_date in (x_date_from + timedelta(n) for n in range(0, x_diff_days + 1, 1)):
# 				_logger.info("chk_date:%s" % chk_date)
# 				if obj_pub_holidays.is_public_holiday(cr, uid, chk_date):
# 					cnt_conflict_days += 1
#
# 			if ((cnt_conflict_days > 0) and (x_days_tmp >= x_diff_days + cnt_conflict_days)):
# 				raise Warning(_('You cannot set a leave request on public holidays.'))
#
# 		return super(hr_holidays, self).create(cr, uid, values, context=context)
