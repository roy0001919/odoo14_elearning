# -*- coding: utf-8 -*-
{
    'name': "BizNavi - Holidays Auto Expired",

    'summary': """
        """,

    'description': """

    """,

    'author': "CENOQ",
    'website': "http://www.cenoq.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_holidays','biznavi'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'templates.xml',
        'biznavi_hr_holidays_expired_data.xml',
        'biznavi_hr_holidays_expired_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}