# -*- coding: utf-8 -*-
{
    'name': "Biznavi Order Sync",

    'summary': "Create sale order from pos order.",

    'description': "Create sale order from pos order.",

    'author': "Cenoq",
    'website': "http://www.cenoq.com",

    'category': 'Point of Sale',
    'version': '1.0',

    'depends': ['biznavi_pos_ticket'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_report_views.xml',
        'views/payment_pos_templates.xml',
        'data/payment_acquirer_data.xml',
        'data/ir_cron.xml',
        # 'data/init_table_seq.xml',
    ],
}