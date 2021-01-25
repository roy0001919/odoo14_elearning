# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 CENOQ Corp.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Taiwan - Accounting",
    "version" : "2.0",
    "category": "Localization/Account Charts",
    "author" : "cenoq.com",
    "maintainer":"cenoq.com",
    "website":"http://www.cenoq.com",
    "description": """
Taiwan - Chart of accounts.
==================================
    """,
    "depends" : ["base", "account"],
    "demo" : [],
    "data" : [
        'account_type.xml',
        'account_chart.xml',
        # 'base_data.xml',
        'account_chart.yml',
    ],
    "license": "GPL-3",
    "auto_install": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

