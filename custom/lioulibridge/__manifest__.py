# -*- coding: utf-8 -*-
{
    'name': "Liou Li Bridge",
    'summary': """
        Liou Li Bridge Customization""",
    'description': """
        Liou Li Bridge Customization
    """,
    'author': "CENOQ",
    'website': "http://www.cenoq.com",
    'category': 'Sales',
    'version': '1.0',
    'depends': ['sale', 'biznavi_ticket'],
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/lioulibridge_report_view.xml',
    ],
    'qweb': [
        'views/qweb_ticket.xml',
    ],
}
