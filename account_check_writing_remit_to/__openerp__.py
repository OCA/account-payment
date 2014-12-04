# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester Alomar <jordi.ballester@eficent.com>
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
    'name': 'Check Writing using Remit-to address',
    'version': '1.0',
    'author': 'Eficent',
    'category': 'Generic Modules/Accounting',
    'description': """
Module to show the remit-to address during the Check Writing and Check Printing.
===============================================================================
    """,
    'website': 'http://www.eficent.com',
    'depends': ['account_check_writing', 'account_voucher_remit_to'],
    'data': [
        'account_check_writing_report.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'active': False,
}
