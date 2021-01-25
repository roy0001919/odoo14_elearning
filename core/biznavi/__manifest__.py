# -*- coding: utf-8 -*-
{
	'name': "BizNavi",

	'summary': """
        BizNavi base.
        """,

	'description': """
        Base module for BizNavi Enterprise Solution.
    """,

	'author': "CENOQ",
	'website': "http://www.cenoq.com",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
	# for the full list
	'category': 'Uncategorized',
	'version': '0.2',

	# any module necessary for this one to work correctly
	'depends': ['web', 'backend_theme_v10', 'res_config_settings_enterprise_remove', 'disable_odoo_online', 'base_technical_features'],

	# always loaded
	'data': [
		# 'security/ir.model.access.csv',
		'data/base.xml',
		'data/res.country.state.csv',
		'security/biznavi_security.xml',
		'templates.xml',
		'res_config_view.xml',
		'wizard/biznavi_update_view.xml',
		'wizard/biznavi_msgbox_view.xml',
		'wizard/translation_writeback_wizard.xml',
		'webclient_templates.xml',
		# 'views/account_res_config.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		'demo.xml',
	],
	'qweb': [
		"static/src/xml/*.xml",
	],
	'application': True,
	'auto_install': True,
	'bootstrap': True,
}
