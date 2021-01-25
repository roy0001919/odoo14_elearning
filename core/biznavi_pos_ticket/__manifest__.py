# -*- coding: utf-8 -*-
{
    'name': "BizNavi POS Ticket",

    'summary': "POS Ticketing System",

    'description': "POS Ticketing System with QR Code",

    'author': "Cenoq Corp.",
    'website': "http://www.cenoq.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale', 'booking_calendar'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_ticket_templates.xml',
        'views/sale_order.xml',
    ],
    'qweb': [
        # 'static/src/xml/notes.xml',
        'static/src/xml/batch.xml',
    ],
}