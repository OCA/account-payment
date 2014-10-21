# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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
    'name': 'Account Voucher Default Writeoff',
    'version': '0.1',
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'AGPL-3',
    'category': 'CRM',
    'summary': 'Change default payment mode when there\'s a writeoff value',
    'description': """
Account Partner is a Company
============================

This module changes the payment option when the writeoff amount is not zero.

Contributors
------------
* Joao Alfredo Gama Batista (joao.gama@savoirfairelinux.com)
""",
    'depends': [
        'account_voucher',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'account_voucher_view.xml',
    ],
    'installable': True,
}
