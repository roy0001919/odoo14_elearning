# -*- coding: utf-8 -*-
{
	'name': "BizNavi - Account",

	'summary': """
		""",

	'description': """
Account Enhanced
	""",

	'author': "CENOQ",
	'website': "http://www.cenoq.com",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
	# for the full list
	'category': 'Accounting & Finance',
	'version': '1.0',

	# any module necessary for this one to work correctly
	'depends': ['account', 'account_accountant', 'biznavi', 'l10n_tw', 'account_financial_report_horizontal'],

	# always loaded
	'data': [
		# 'security/ir.model.access.csv',
		# 'data/account_financial_report_data.xml',
		# 'wizard/account_financial_report_view.xml',
		# 'views/account_report.xml',
		# 'views/report_financial.xml',
		# 'views/report_financial_horizontal.xml',
		# 'data/report_paperformat.xml',
		# 'data/ir_actions_report_xml.xml',
	],
}


