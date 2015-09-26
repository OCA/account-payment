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
    'name': 'Paybox',
    'version': '0.1',
    'sequence': 150,
    'category': 'Custom',
    'description': """Paybox payment acquirer (France)""",
    'author': 'Anybox',
    'website': 'www.anybox.fr',
    'depends': [
        'payment',
        'l10n_fr'
    ],
    'data': [
        'paybox_data.xml',
        'view/paybox.xml',
        'data/template.xml',
    ],
    'demo_xml': [
    ],
    'init_xml': [
    ],
    'css': [],
    'icon': '',
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'post_load': None,
    }
