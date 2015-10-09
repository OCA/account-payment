# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2010 - 2014 Savoir-faire Linux
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

# NOTE: The name of the supplied field was initially "display_name", but it
# seems that Odoo, whenever it seems "name" in the field, returns the value for
# "name". Well...

{
    'name': 'Display name for currencies',
    'version': '8.0.1.0.0',
    'author': "Savoir-faire Linux,Odoo Community Association (OCA)",
    'website': 'http://www.savoirfairelinux.com',
    'category': 'Generic Modules/Accounting',
    'license': 'AGPL-3',
    'description': """
Supply res.currency.print_on_check
==================================

This module improves res.currency by adding the "print_on_check" field, which
stores the human readable name of the currency (US Dollar, Euro, Canadian
Dollar, etc.)

Contributors
------------
* Joao Alfredo Gama Batista <joao.gama@savoirfairelinux.com>
* Virgil Dupras <virgil.dupras@savoirfairelinux.com>
* Sandy Carter <sandy.carter@savoirfairelinux.com>
* Primaco <info@primaco.ca>
""",
    'depends': ['base'],
    'data': [
        'currency_view.xml',
        'currency_data.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
}
