# -*- coding: utf-8 -*-
{
    'name': "The Eye of Gang Shan",
    'summary': """
        The Eye of Gang Shan""",
    'description': """
        The Eye of Gang Shan Customization
    """,
    'author': "CENOQ",
    'website': "http://www.cenoq.com",
    'category': 'Sales',
    'version': '1.0',
    'depends': ['sale', 'biznavi_ticket'],
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/gangshan_report_view.xml',
        'views/sale_order_email_template.xml',
        'views/views.xml',
    ],
    'qweb': [
        'views/qweb_ticket.xml',
    ],
}
