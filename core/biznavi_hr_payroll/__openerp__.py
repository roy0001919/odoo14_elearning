# -*- coding: utf-8 -*-
{
    'name': "BizNavi - Taiwan Payroll",

    'summary': """
    Taiwan Payroll Rules.
        """,

    'description': """
        1.Labor insurance(Class 1,5,6)
        2.Health insurance(Class 1)
        3.Second-generation health insurance paid by company(Supplementary premiums)
        4.Personal allocate
    """,

    'author': "CENOQ",
    'website': "http://www.cenoq.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['hr_payroll', 'biznavi'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/l10n_zh_tw_hr_payroll.xml',
        'data/l10n_zh_tw_hr_payroll_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}