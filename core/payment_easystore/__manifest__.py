# -*- coding: utf-8 -*-
{
    'name': "payment_easystore",
    'summary': 'Payment Acquirer: Sinopac Transfer Implementation',
    'description': """Sinopac Transfer Payment Acquirer""",
    'author': "CENOQ Corp.",
    'website': "http://www.cenoq.com",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['payment', 'biznavi_payment_transaction'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_easystore_templates.xml',
        'views/payment_easystore_views.xml',
        'data/payment_acquirer_data.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
}