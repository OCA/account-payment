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

__authors__ = [
    "Luis Manuel Angueira Blanco (Pexego) <manuel@pexego.es",
    "Borja López Soilán (Pexego) <borjals@pexego.es>"
]

from osv import osv, fields

class account_journal(osv.osv):
    """
    Extends the account journals to add the show_in_cash_statements field.
    """
    _inherit = 'account.journal'

    _columns = {
        'show_in_cash_statements': fields.boolean('Show in Cash Statements', help="If enabled, this journal will be available on the Entries by Cash Statements."),
    }

    _defaults = {
        'show_in_cash_statements': lambda *a : False
    }

account_journal()


class cash_statement_line_type(osv.osv):
    """
    Cash Statement Line Type.
    """
    _name = 'account.bank.statement.line.type'
    _description = "Cash Statement Line Type"

    _columns = {
        'type': fields.selection([('in', 'Deposit'), ('out', 'Withdrawal')], 'Type', required=True),
        'code': fields.char('Code', size=16, required=True, select=1),
        'name': fields.char('Name', size=64, required=True),

        'account_id': fields.many2one('account.account', 'Account', domain="[('type', '!=', 'view')]"),
        'partner_id': fields.many2one('res.partner', 'Partner'),
    }

cash_statement_line_type()


class cash_statement(osv.osv):
    """
    Extend the bank statement add the Cash Statements fields and behaviour.
    """
    _inherit = 'account.bank.statement'

    def _get_cash_statement(self, cr, uid, ids, field_name, arg, context=None):
        """
        Get whether it is a cash statement.
        """
        if not context: context = {}
        res = {}
        for statement in self.browse(cr, uid, ids, context=context):
            res[statement.id] = (statement.journal_id and statement.journal_id.show_in_cash_statements) or False
        return res

    
    _columns = {
        'cash_statement':  fields.function(_get_cash_statement, method=True, type='boolean', string="Cash Statement",
                store={
                    'account.bank.statement': (lambda self, cr, uid, ids, context: ids, ['journal_id'], 10),
                    'account.journal': (lambda self, cr, uid, ids, context: self.pool.get('account.bank.statement').search(cr, uid, [('journal_id', 'in', ids)], context=context), ['show_in_cash_statements'], 20)
                }),
    }

    _defaults = {
    }

    def cash_statement_on_change_date(self, cr, uid, ids, date, context=None):
        """
        Set the period when the date changes.
        """
        res = {}
        if date:
            periods = self.pool.get('account.period').find(cr, uid, date, context=context)
            if periods:
                res['period_id'] = periods[0]

        return { 'value': res }

cash_statement()



class cash_statement_line(osv.osv):
    """
    Extend the bank statement lines to add the cash-specific fields
    and behaviour.
    """
    _inherit = 'account.bank.statement.line'

    _columns = {
        'name': fields.char('Name', size=128, required=True), # Longer description
        'line_type_id': fields.many2one('account.bank.statement.line.type', 'Type'),
    }

    def cash_line_on_change_amount(self, cr, uid, ids, line_type_id, amount, context=None):
        """
        Force withdrawal movements to be negative and deposit ones to
        be positive.
        """
        if line_type_id:
            line_type = self.pool.get('account.bank.statement.line.type').browse(cr, uid, line_type_id, context=context)
            if line_type.type == 'out':
                amount = -abs(amount)
            elif line_type.type == 'in':
                amount = abs(amount)

        return { 'value': { 'amount': amount } }


    def cash_line_on_change_partner_id(self, cr, uid, ids, type, partner_id):
        """
        Set the partner account when the partner changes, depending on the 
        line type.
        """
        res = {}
        
        if type and partner_id:
            partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if type == 'supplier':
                res['account_id'] = partner_obj.property_account_payable.id
            elif type == 'customer':
                res['account_id'] = partner_obj.property_account_receivable.id
                
        return { 'value': res }


    def cash_line_on_change_line_type_id(self, cr, uid, line_id, partner_id, original_type, line_type_id, context=None):
        """
        Update the type, account and partner when the line type changes.
        """
        res = {}

        if line_type_id:
            line_type = self.pool.get('account.bank.statement.line.type').browse(cr, uid, line_type_id)

            #
            # Set the type
            #
            if line_type.type == 'in':
                res['type'] = 'customer'
            elif line_type.type == 'out':
                res['type'] = 'supplier'
            else:
                res['type'] = 'general'

            # Set the default description
            res['name'] = line_type.name

            #
            # Set the account and partner
            #
            if partner_id:
                account_id = self.cash_line_on_change_partner_id(cr, uid, line_id, res['type'], partner_id)
                res.update(account_id['value'])
            else:
                res['account_id'] = line_type.account_id and line_type.account_id.id or None
                res['partner_id'] = line_type.partner_id and line_type.partner_id.id or None
                
        return { 'value': res }

cash_statement_line()

