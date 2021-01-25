# -*- coding: utf-8 -*-
{
    'name': "New Xi Kou Bridge",
    'summary': """
        New Xi Kou Bridge""",
    'description': """
        New Xi Kou Bridge Customization
    """,
    'author': "CENOQ",
    'website': "http://www.cenoq.com",
    'category': 'Sales',
    'version': '1.0',
    'depends': ['sale', 'biznavi_ticket'],
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/xikoubridge_report_view.xml',
        'views/sale_order_email_template.xml',
    ],
    'qweb': [
        'views/qweb_ticket.xml',
    ],
}
