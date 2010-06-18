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
Extensions to the bank statements to add analytical accounting features.
"""

__authors__ = [
    "Borja López Soilán (Pexego) <borjals@pexego.es>"
]

from osv import osv, fields


class bank_statement(osv.osv):
    """
    Extend the bank statement to add the analytic account when creating
    the accounting moves.
    """
    _inherit = 'account.bank.statement'

    def button_confirm(self, cr, uid, ids, context={}):
        """
        Extend the button confirm action, to add the analytic account references
        to the account move lines being created.
        """
        super(bank_statement, self).button_confirm(cr, uid, ids, context=context)
        aml_facade = self.pool.get('account.move.line')
        for st in self.browse(cr, uid, ids, context):
            for st_line in st.line_ids:
                if st_line.analytic_account_id:
                    for move in st_line.move_ids:
                        for line in move.line_id:
                            if line.account_id == st_line.account_id:
                                aml_facade.write(cr, uid, [line.id], {
                                        'analytic_account_id': st_line.analytic_account_id.id
                                    })

bank_statement()



class bank_statement_line(osv.osv):
    """
    Extend the bank statement to add the analytic account reference.
    """
    _inherit = 'account.bank.statement.line'

    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
    }

bank_statement_line()

