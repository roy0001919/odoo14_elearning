# -*- coding: utf-8 -*-
{
    'name': "BizNavi - Taiwan Computer Invoice",

    'summary': """
        """,

    'description': """
Taiwan Computer Invoice
    """,

    'author': "CENOQ",
    'website': "http://www.cenoq.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'biznavi', 'sale_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'view.xml',
        'biznavi_computer_invoice_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}