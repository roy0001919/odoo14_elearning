# -*- coding: utf-8 -*-
{
    'name': "BizNavi - MRP",

    'summary': """
        Enhanced MRP.
        """,

    'description': """
        Add product qty into Bill of Materials Structure.
    """,

    'author': "CENOQ",
    'website': "http://www.cenoq.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Manufacturing',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['biznavi', 'mrp'],

    # always loaded
    'data': [
        'views/mrp_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}