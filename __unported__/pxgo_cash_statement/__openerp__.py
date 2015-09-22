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
        "name" : "Pexego - Cash Statements",
        "version" : "1.0",
        "author" : "Pexego for Igalia (http://www.igalia.com/),Odoo Community Association (OCA)",
        "website" : "http://www.pexego.es",
        "license": "GPL-3 or any later version",
        "category" : "Enterprise Specific Modules",
        "description": """
Module for easier cash management.

Adds an "Entries by Cash Statement" view of the bank statements that shows only
the fields required for cash management.
It works with "Cash Statement Line Types" that allow to predefine cash lines
(pre-set the account, type [withdrawal/deposit], and description of the cash
statement line), so the user doesn't have to cope with those details
(even more, if the user introduces an invalid quantity, for example a positive
amount for a withdrawal, OpenERP will automatically correct the entry).
            """,
        "depends" : [
                'base',
                'account',
            ],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                'account_journal_view.xml',
                'cash_statement_view.xml',
            ],
        "installable": False,
        'active': False

}

