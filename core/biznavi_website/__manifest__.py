# -*- coding: utf-8 -*-
{
    "name": "BizNavi Website",
    "version": "1.0",
    "author": "CENOQ Corperation",
    "website": "http://www.cenoq.com",
    "category": "Website",
    "summary": "Website Sale Enhancement & Localization",
    "depends": ['biznavi', 'website'],
    'data': [
        'security/biznavi_website_security.xml',
        'security/ir.model.access.csv',
        'website_templates.xml',
        'announcement_view.xml',
    ],
    "installable": True
}
