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
        "name" : "Pexego - Analytic in Bank Statements",
        "version" : "1.0",
        "author" : "Pexego for Igalia (http://www.igalia.com/),Odoo Community Association (OCA)",
        "website" : "http://www.pexego.es",
        "license": "GPL-3 or any later version",
        "category" : "Enterprise Specific Modules",
        "description": """
Extends the Bank Statements to add support for analytic accounting.

A analytic account field will be added to bank statement lines, allowing
the user to directly register small expenses or incomes on analytic accounts.

This may be useful for petty cash management.
            """,
        "depends" : [
                'base',
                'account',
                #'analytic',
            ],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                'bank_statement_view.xml',
            ],
        "installable": False,
        'active': False

}

