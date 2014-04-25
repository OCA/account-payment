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
"""
Extension of the bank statement lines to add running totals.
"""

__authors__ = [
    "Borja López Soilán (Pexego) <borjals@pexego.es>"
]

from osv import osv, fields

class bank_statement_line(osv.osv):
    """
    Extend the bank statement lines to add running totals.
    """
    _inherit = 'account.bank.statement.line'
    
    def _get_running_balance(self, cr, uid, ids, name, args, context):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0
            statement = line.statement_id
            running_balance = statement.balance_start
            for st_line in statement.line_ids:
                running_balance += st_line.amount
                if st_line.id == line.id:
                    res[line.id] = running_balance
                    break
        return res

    _columns = {
        'running_balance': fields.function(_get_running_balance, method=True, string="Running Balance"),
    }

bank_statement_line()

