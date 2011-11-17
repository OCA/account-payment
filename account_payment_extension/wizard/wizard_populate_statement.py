# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import wizard
import pooler
from tools.misc import UpdateableStr

FORM = UpdateableStr()

FIELDS = {
    'lines': {'string': 'Payment Lines', 'type': 'many2many',
        'relation': 'payment.line'},
}

def _search_entries(obj, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    line_obj = pool.get('payment.line')
    statement_obj = pool.get('account.bank.statement')

    statement = statement_obj.browse(cr, uid, data['id'], context=context)

    line_ids = line_obj.search(cr, uid, [
        ('move_line_id.reconcile_id', '=', False),
        ('order_id.mode.journal.id', '=', statement.journal_id.id)])
    line_ids.extend(line_obj.search(cr, uid, [
        ('move_line_id.reconcile_id', '=', False),
        ('order_id.mode', '=', False)]))

    FORM.string = '''<?xml version="1.0"?>
<form string="Populate Statement:">
    <field name="lines" colspan="4" height="300" width="800" nolabel="1"
        domain="[('id', 'in', [%s])]"/>
</form>''' % (','.join([str(x) for x in line_ids]))
    return {}

def _populate_statement(obj, cr, uid, data, context):
    line_ids = data['form']['lines'][0][2]
    if not line_ids:
        return {}

    pool = pooler.get_pool(cr.dbname)
    line_obj = pool.get('payment.line')
    statement_obj = pool.get('account.bank.statement')
    statement_line_obj = pool.get('account.bank.statement.line')
    currency_obj = pool.get('res.currency')
    move_line_obj = pool.get('account.move.line')
    voucher_obj = pool.get('account.voucher')
    voucher_line_obj = pool.get('account.voucher.line')

    statement = statement_obj.browse(cr, uid, data['id'], context=context)

    for line in line_obj.browse(cr, uid, line_ids, context=context):
        ctx = context.copy()
        ctx['date'] = line.ml_maturity_date
        amount_currency = line.type == 'payment' and line.amount_currency or -line.amount_currency
        amount = currency_obj.compute(cr, uid, line.currency.id,
                statement.currency.id, amount_currency, context=ctx)

        voucher_id = False
        if line.move_line_id:
            #We have to create a voucher and link it to the bank statement line
            context.update({'move_line_ids': [line.move_line_id.id]})
            result = voucher_obj.onchange_partner_id(cr, uid, [], partner_id=line.move_line_id.partner_id.id,
                journal_id=statement.journal_id.id, price=abs(amount), currency_id= statement.currency.id,
                ttype=(amount < 0 and 'payment' or 'receipt'), date=line.date or line.move_line_id.date, context=context)

            voucher_res = { 'type':(amount < 0 and 'payment' or 'receipt'),
                            'name': line.move_line_id.name,
                            'reference': (line.order_id.reference or '?') +'. '+ line.name,
                            'partner_id': line.move_line_id.partner_id.id,
                            'journal_id': statement.journal_id.id,
                            'account_id': result.get('account_id', statement.journal_id.default_credit_account_id.id), # improve me: statement.journal_id.default_credit_account_id.id
                            'company_id': statement.company_id.id,
                            'currency_id': statement.currency.id,
                            'date': line.date or line.move_line_id.date,
                            'amount': abs(amount),
                            'period_id': statement.period_id.id}
            voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)

            voucher_line_dict =  {}
            if result['value']['line_ids']:
                for line_dict in result['value']['line_ids']:
                    move_line = move_line_obj.browse(cr, uid, line_dict['move_line_id'], context)
                    if line.move_line_id.move_id.id == move_line.move_id.id:
                        voucher_line_dict = line_dict
            if voucher_line_dict:
                voucher_line_dict.update({'voucher_id': voucher_id, 'amount': abs(amount)})
                voucher_line_obj.create(cr, uid, voucher_line_dict, context=context)

        statement_line_obj.create(cr, uid, {
            'name': (line.order_id.reference or '?') +'. '+ line.name,
            # Tipically: type=='payable' => amount>0  type=='receivable' => amount<0
            'amount': line.type == 'payable' and amount or -amount,
            'type': line.order_id.type=='payable' and 'supplier' or 'customer',
            'partner_id': line.partner_id.id,
            'account_id': line.move_line_id.account_id.id,
            'statement_id': statement.id,
            'ref': line.communication,
            'voucher_id': voucher_id,
            }, context=context)
    return {}


class PopulateStatement(wizard.interface):
    """
    Populate the current statement with selected payement lines
    """
    states = {
        'init': {
            'actions': [_search_entries],
            'result': {
                'type': 'form',
                'arch': FORM,
                'fields': FIELDS,
                'state': [
                    ('end', '_Cancel'),
                    ('add', '_Add', '', True)
                ]
            },
        },
        'add': {
            'actions': [],
            'result': {
                'type': 'action',
                'action': _populate_statement,
                'state': 'end'
            },
        },
    }

PopulateStatement('populate_statement_ext')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

