# -*- coding: utf-8 -*-
{
    'name': 'E.Sun Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: E.Sun Implementation',
    'version': '1.0',
    'description': """E.Sun Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_esun_templates.xml',
        'views/payment_esun_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}