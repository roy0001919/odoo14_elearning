# -*- coding: utf-8 -*-
{
    'name': 'Sinopac Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Sinopac Implementation',
    'version': '1.0',
    'description': """Sinopac Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_sinopac_templates.xml',
        'views/payment_sinopac_views.xml',
        'data/payment_acquirer_data.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
}