# -*- coding: utf-8 -*-
{
    'name': "Biznavi Payment Transaction",

    'summary': """
        Biznavi Payment Transaction for Booking""",

    'description': """
        Biznavi Payment Transaction for Booking
    """,

    'author': "CENOQ",
    'website': "http://www.cenoq.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['payment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'wizard/payment_transaction_wizard.xml',
        'views/payment_transaction_views.xml',
    ],
}