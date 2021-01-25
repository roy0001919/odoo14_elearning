# -*- coding: utf-8 -*-
{
    'name': "BizNavi - Taiwan VAT Number Validation",

    'summary': """
        """,

    'description': """
        Taiwan VAT validation for Partner's VAT numbers.
    """,

    'author': "Boyce Huang",
    'website': "http://www.cenoq.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hidden/Dependency',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base_vat', 'biznavi'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'res_config_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}