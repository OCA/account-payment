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
    "name": "Account voucher display writeoff",
    "version": "1.0r089",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "category": 'Accounting & Finance',
    'complexity': "normal",
    "description": """
Display writeoff options on sale or purchase vouchers. Without setting these
options explicitely, if a payment difference is encountered on vouchers of these
types, it is booked on the account payable or account receivable which can pose
problems for automatic reconciliation.

This addon also enables setting the voucher type as a selection criterium for
default values, so that you can set different default values for writeoff
settings for different voucher types.

At Therp, we use this functionality to write off small rounding differences
when applying an inclusive tax on purchase vouchers. This is currently
depending on lp:827649 for which we are proposing a fix.
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
