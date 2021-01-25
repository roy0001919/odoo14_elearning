# -*- coding: utf-8 -*-

{
    'name': 'allPay Payment Acquirer',
    'category': 'Website',
    'summary': 'Payment Acquirer: allPay Implementation',
    'version': '1.0',
    'description': """allPay Payment Acquirer""",
    'author': 'CENOQ Corporation',
    'depends': ['payment'],
    'data': [
        'views/allpay.xml',
        'views/payment_acquirer.xml',
        'data/allpay.xml',
    ],
    'installable': True,
    'price': 500,
    'currency': 'USD',
}
