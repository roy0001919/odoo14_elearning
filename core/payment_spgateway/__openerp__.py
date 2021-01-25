# -*- coding: utf-8 -*-

{
    'name': 'Spgateway Payment Acquirer',
    'category': 'Website',
    'summary': 'Payment Acquirer: Spgateway Implementation',
    'version': '1.0',
    'description': """Spgateway Payment Acquirer""",
    'author': 'CENOQ Corporation',
    'depends': ['payment'],
    'data': [
        'views/spgateway.xml',
        'views/payment_acquirer.xml',
        'data/spgateway.xml',
    ],
    'installable': True,
    'price': 500,
    'currency': 'USD',
}