# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2012 Therp BV (<http://therp.nl>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Account voucher tax filter",
    "version": "1.0r028",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "category": 'Accounting & Finance',
    'complexity': "normal",
    "description": """
This module adds dynamic filters on sale and purchase vouchers so that
sale taxes cannot be used on purchase vouchers and vice versa.

This addon is compatible with OpenERP 6.1. In OpenERP 7.0, the tax
selection has been added to the specific views for sale and purchase taxes.
For the generic view, the missing filter has been reported as lp:1081097 and
a solution has been proposed. Note that you should probably avoid using the
generic view to create sale or purchase vouchers anyway due to lp:1080840
    """,
    'website': 'http://therp.nl',
    'images': [],
    'depends': ['account_voucher'],
    'data': [
        'view/account_voucher.xml',
    ],
    "license": 'AGPL-3',
    "installable": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
