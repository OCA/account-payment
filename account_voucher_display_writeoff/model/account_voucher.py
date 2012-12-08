# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module Copyright (C) 2012 Therp BV (<http://therp.nl>).
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

from openerp.osv import osv, fields


class account_voucher(osv.Model):
    """
    Add the voucher's type as a selection criterium for 
    default values by setting change_default to True.
    Now you can use appropriate defaults
    for e.g. write off settings per voucher type.
    """
    _inherit = 'account.voucher'
    _columns = {
        'type': fields.selection(
            [
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
            ('payment', 'Payment'),
            ('receipt', 'Receipt'),
            ], 'Default Type', readonly=True, states={'draft': [('readonly', False)]},
            change_default=1),
        }
