# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from datetime import datetime
import logging

# 勞保設定值
wi_range = [20008,20100,21000,21900,22800,24000,25200,26400,27600,28800,30300,31800,33300,34800,36300,38200,40100,42000,43900]
wi_rate = 0.09
wi_dam_rate = 0.01

# 健保設定值
hi_range = [20008,20100,21000,21900,22800,24000,25200,26400,27600,28800,30300,31800,33300,34800,36300,38200,40100,42000,43900,45800,48200,50600,53000,55400,57800,60800,63800,66800,69800,72800,76500,80200,83900,87600,92100,96600,101100,105600,110110,115500,120900,126300,131700,137100,142500,147900,150000,156400,162800,169200,175600,18200]
hi_rate = 0.0491

_logger = logging.getLogger(__name__)


class HrContractBe(models.Model):
	_name = 'hr.contract'
	_inherit = 'hr.contract'

	raise_amount = fields.Integer(default=0, string='Dependents Number')
	wi_join_date = fields.Date(default=fields.Date.today, string='Labor insurance join day')
	wi_self_provide_rate = fields.Float(string='Individual retirement pay')

	@api.constrains('wi_self_provide_rate')
	def _check_max_provide_rate(self):
		for record in self:
			if record.wi_self_provide_rate > 0.06:
				raise ValidationError(_('Individual retirement pay can not be greater than 6%(0.06)'))

	def _get_wi(self, payslip_date_to):
		in_date_to = datetime.strptime(payslip_date_to, '%Y-%m-%d').date()
		x_wi_join_date = datetime.strptime(self.wi_join_date, '%Y-%m-%d').date()
		diff_days = (in_date_to - x_wi_join_date).days
		if diff_days > 30:
			diff_days = 30

		wi_real_wage = wi_range[-1]
		for i in range(len(wi_range)):
			if self.wage > wi_range[i]:
				pass
			else:
				wi_real_wage = wi_range[i]
				break

		return wi_real_wage * diff_days / 30

	def get_wi_1(self, payslip_date_to):
		wi_real_wage = self._get_wi(payslip_date_to)
		wi_gen = wi_real_wage * wi_rate
		wi_dam = wi_real_wage * wi_dam_rate
		wi = -1 * round(wi_gen * 0.2 + wi_dam * 0.2)

		return wi

	def get_wi_5(self, payslip_date_to):
		wi_real_wage = self._get_wi(payslip_date_to)
		wi_gen = wi_real_wage * wi_rate
		wi = -1 * round(wi_gen * 0.8)

		return wi

	def get_wi_6(self, payslip_date_to):
		return self.get_wi_1(payslip_date_to)

	def get_wi_sp(self, payslip_date_to):
		wi_real_wage = self._get_wi(payslip_date_to)

		return -1 * wi_real_wage * self.wi_self_provide_rate

	def get_hi_1(self):
		x_raise = self.raise_amount
		if x_raise >= 3:
			x_raise = 4
		else:
			x_raise = 1 + x_raise

		hi_real_wage = hi_range[-1]
		for i in range(len(hi_range)):
			if self.wage > hi_range[i]:
				pass
			else:
				hi_real_wage = hi_range[i]
				break

		hi = -1 * round(hi_real_wage * hi_rate * 0.3) * x_raise
		return hi

	def get_preded_tax(self):
		x_wage = int((self.wage-1)/500)*500
		x_raise = self.raise_amount
		annual = x_wage * 12
		free = (1 + x_raise) * 85000
		std_raise = 180000
		spc_raise = 128000

		v1 = annual - (free + std_raise + spc_raise)

		v2 = 0
		if v1 <= 520000:
			v2 = round(v1 * 0.05) - 0
		elif 520001 <= v1 <= 1170000:
			v2 = round(v1 * 0.12) - 36400
		elif 1170001 <= v1 <= 2350000:
			v2 = round(v1 * 0.2) - 130000
		elif 2350001 <= v1 <= 4400000:
			v2 = round(v1 * 0.3) - 365000
		elif 4400001 <= v1:
			v2 = round(v1 * 0.4) - 805000

		v3 = int(v2/12/10) * 10
		return v3 if v3 > 2000 else 0

	# 公司部份
	def get_comp_exinsu(self, gross_value):
		hi_real_wage = hi_range[-1]
		for i in range(len(hi_range)):
			if self.wage > hi_range[i]:
				pass
			else:
				hi_real_wage = hi_range[i]
				break

		rtnval = (gross_value - hi_real_wage) * 0.02
		return rtnval if (rtnval > 0) else 0

	def get_wi_comp_retire(self, payslip_date_to):
		wi_real_wage = self._get_wi(payslip_date_to)

		return 0.06 * wi_real_wage

	def get_wi_1_comp(self, payslip_date_to, dam_rate):
		wi_real_wage = self._get_wi(payslip_date_to)
		wi_gen = wi_real_wage * wi_rate
		wi_dam = wi_real_wage * wi_dam_rate
		wi = round(wi_gen * 0.7 + wi_dam * 0.7 + (wi_real_wage * dam_rate /100))

		return wi

	def get_hi_1_comp(self):
		hi_real_wage = hi_range[-1]
		for i in range(len(hi_range)):
			if self.wage > hi_range[i]:
				pass
			else:
				hi_real_wage = hi_range[i]
				break

		hi = round(hi_real_wage * hi_rate * 0.6)
		return hi
