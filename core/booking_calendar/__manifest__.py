# -*- coding: utf-8 -*-
{
    'name': "Resource booking calendar backend",
    'version': '1.0.0',
    'author': 'CENOQ Corporation',
    'website': 'https://www.cenoq.com',
    'category': 'Sale',
    'depends': ['resource', 'sale', 'web_widget_color', 'web_calendar_repeat_form', 'web_calendar_quick_navigation'],
    'data': [
        'views.xml',
        'report_saleorder.xml',
    ],
    'qweb': [
        'static/src/xml/booking_calendar.xml',
    ],
    'installable': True
}
