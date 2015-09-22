# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2010 Pexego Sistemas Informáticos. All Rights Reserved
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
        "name" : "Pexego - Running balance in Bank Statements",
        "version" : "1.0",
        "author" : "Pexego for Igalia (http://www.igalia.com/),Odoo Community Association (OCA)",
        "website" : "http://www.pexego.es",
        "license": "GPL-3 or any later version",
        "category" : "Enterprise Specific Modules",
        "description": """
Adds a running balance (running total) column to the bank statement lines.
This makes it easier to find differences and mistakes in long statements.
            """,
        "depends" : [
                'base',
                'account',
            ],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                'bank_statement_view.xml',
            ],
        "installable": False,
        'active': False

}

