# -*- coding: utf-8 -*-
{
    'name': 'Biznavi Ticket',
    'version': '0.1',
    'author': 'CENOQ Corporation',
    'website': 'https://www.cenoq.com',
    'category': 'Website',
    'depends': ['biznavi_website', 'website_booking_calendar'],
    'data': [
        'report/sale_order_line_report.xml',
        'report/sale_order_line_report_templates.xml',
        'views/sale_order.xml',
        'views/views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
