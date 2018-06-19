# coding: utf-8
# ==============================================================================
#
#    Paybox module for OpenERP, Snesup
#    Copyright (C) 2013 ANYBOX (<http://www.anybox.fr>)
#
#    This file is a part of paybox
#
#    paybox is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    paybox is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
# ==============================================================================

{
    'name': 'Paybox payment acquirer',
    'version': '8.0.1.0.0',
    'sequence': 150,
    'category': 'Hidden',
    'author': 'Odoo Community Association (OCA), Jean-Baptiste Quenot, Florent Jouatte (Anybox)',
    'summary': "Payment acquirer: Paybox implementation",
    'depends': [
        'payment'
    ],
    'data': [
        'templates/payment_acquirer.xml',
        'data/payment_acquirer.xml',
        'views/payment_acquirer.xml',
    ],
    'css': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
