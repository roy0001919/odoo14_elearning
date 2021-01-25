# -*- coding: utf-8 -*-
{
    'name': 'ibon Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: ibon Implementation',
    'version': '1.0',
    'description': """ibon Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_ibon_templates.xml',
        'data/payment_acquirer_data.xml',
        'data/ir_cron.xml',
        'views/payment_ibon_views.xml',
    ],
    'installable': True,
}