# -*- coding: utf-8 -*-
# Copyright 2015 Holger Brunn <hbrunn@therp.nl>
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Excel Style Grid",
    "version": "10.0.1.0.0",
    "author": "CENOQ Corperation",
    "category": "Hidden/Dependency",
    "summary": "x2many field as grid",
    "depends": [
        'web',
    ],
    "data": [
        'views/templates.xml',
    ],
    "qweb": [
        'static/src/xml/web_widget_grid.xml',
    ],
    "installable": True,
}