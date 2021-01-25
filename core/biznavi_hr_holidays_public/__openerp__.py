# -*- coding: utf-8 -*-
{
    'name': "BizNavi - Public Holidays",

    'summary': """
        """,

    'description': """
Manage Public Holidays
======================
    """,

    'author': "CENOQ",
    'website': "http://www.cenoq.com",
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['hr', 'hr_holidays', 'biznavi'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_holidays_public_view.xml',
    ],
    'demo': [
        'demo.xml',
    ],
}