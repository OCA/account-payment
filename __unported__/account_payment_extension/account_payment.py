# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#                    All Rights Reserved.Jordi Esteve <jesteve@zikzakmedia.com>
# AvanzOSC, Avanzed Open Source Consulting
# Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
# Copyright (C) 2013 Akretion Ltda ME (www.akretion.com) All Rights Reserved
# Renato Lima <renato.lima@akretion.com.br>
# $Id$
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _


class payment_type(orm.Model):
    _name = 'payment.type'
    _description = 'Payment type'
    _columns = {
        'name': fields.char('Name', size=64, required=True,
            help='Payment Type', translate=True),
        'code': fields.char('Code', size=64, required=True,
            help='Specify the Code for Payment Type'),
        'suitable_bank_types': fields.many2many(
            'res.partner.bank.type', 'bank_type_payment_type_rel',
            'pay_type_id', 'bank_type_id', 'Suitable bank types'),
        'active': fields.boolean('Active', select=True),
        'note': fields.text('Description', translate=True,
            help="""Description of the payment type that will be shown in
                the invoices"""),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'active': True,
        'company_id': lambda self, cr, uid, c: self.pool.get(
            'res.users').browse(cr, uid, uid, c).company_id.id
    }


class payment_mode(orm.Model):
    _inherit = 'payment.mode'
    _columns = {
        'type': fields.many2one('payment.type', 'Payment type', required=True,
            help='Select the Payment Type for the Payment Mode.'),
        'require_bank_account': fields.boolean('Require Bank Account',
            help="""Ensure all lines in the payment order have a bank
                account when proposing lines to be added in the
                payment order."""),
        'require_received_check': fields.boolean('Require Received Check',
            help="""Ensure all lines in the payment order have the
                Received Check flag set."""),
        'require_same_bank_account': fields.boolean(
            'Require the Same Bank Account', help="""Ensure all lines in the
                payment order and the payment mode have the same
                account number."""),
    }
    _defaults = {
        'require_bank_account': False,
    }


class payment_order(orm.Model):
    _inherit = 'payment.order'

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('type', 'payable')

    def _get_reference(self, cr, uid, context=None):
        if context is None:
            context = {}
        PAYMENT_MODEL = {
            'payable': 'payment.order', 'receivable': 'rec.payment.order'}
        model = PAYMENT_MODEL.get(context.get('type', 'payable'))
        return self.pool.get('ir.sequence').get(cr, uid, model)

    def _get_period(self, cr, uid, context=None):
        try:
            # find() function will throw an exception if no period can be
            # found for current date. That should not be a problem because
            # user would be notified but as this model inherits an existing
            # one, once installed it will create the new field and try to
            # update existing records (even if there are no records yet)
            # So we must ensure no exception is thrown, otherwise the
            # module can only be installed once periods are created.
            periods = self.pool.get('account.period').find(cr, uid)
            return periods[0]
        except Exception:
            return False

    def _payment_type_name_get(self, cr, uid, ids, field_name,
                            arg, context=None):
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = rec.mode and rec.mode.type.name or ""
        return result

    def _name_get(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = rec.reference
        return result

    _columns = {
        'type': fields.selection([
            ('payable', 'Payable'),
            ('receivable', 'Receivable'),
            ], 'Type', readonly=True, select=True),
        # invisible field to filter payment order lines by payment type
        'payment_type_name': fields.function(
            _payment_type_name_get, method=True, type="char", size=64,
            string="Payment type name"),
        # The field name is necessary to add attachement documents to
        # payment orders
        'name': fields.function(
            _name_get, method=True, type="char", size=64, string="Name"),
        'create_account_moves': fields.selection(
            [('bank-statement', 'Bank Statement'),
            ('direct-payment', 'Direct Payment')], 'Create Account Moves',
            required=True, states={'done': [('readonly', True)]},
            help="""Indicates when account moves should be created for
            order payment lines. 'Bank Statement' will wait until user
            introduces those payments in bank a bank statement.
            'Direct Payment' will mark all payment lines as payied once
            the order is done."""),
        'period_id': fields.many2one('account.period', 'Period',
            states={'done': [('readonly', True)]}),
    }
    _defaults = {
        'type': _get_type,
        'reference': _get_reference,
        'create_account_moves': lambda *a: 'bank-statement',
        'period_id': _get_period,
    }

    def cancel_from_done(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        #Search for account_moves
        remove = []
        for move in self.browse(cr, uid, ids, context=context):
            #Search for any line
            for move_line in move.line_ids:
                if move_line.payment_move_id:
                    remove.append(move_line.payment_move_id.id)

        self.pool.get('account.move').button_cancel(
            cr, uid, remove, context=context)
        self.pool.get('account.move').unlink(cr, uid, remove, context)
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        pay_orders = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for t in pay_orders:
            if t['state'] in ('draft', 'cancel'):
                unlink_ids.append(t['id'])
            else:
                raise orm.except_orm(
                    _('Invalid action!'),
                    _("""You cannot delete payment order(s) which are
                        already confirmed or done!"""))
        result = super(payment_order, self).unlink(
            cr, uid, unlink_ids, context=context)
        return result

    def set_done(self, cr, uid, ids, context=None):
        result = super(payment_order, self).set_done(cr, uid, ids, context)

        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        payment_line_obj = self.pool.get('payment.line')

        currency = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.currency_id
        company_currency_id = currency.id

        for order in self.browse(cr, uid, ids, context):
            if order.create_account_moves != 'direct-payment':
                continue

            # This process creates a simple account move with
            # bank and line accounts and line's amount. At the end
            # it will reconcile or partial reconcile both entries
            # if that is possible.
            move_id = self.pool.get('account.move').create(cr, uid, {
                'name': '/',
                'journal_id': order.mode.journal.id,
                'period_id': order.period_id.id,
            }, context)

            for line in order.line_ids:
                if not line.amount:
                    continue

                if not line.account_id:
                    raise orm.except_orm(
                        _('Error!'),
                        _("""Payment order should create account moves
                            but line with amount %.2f for partner "%s" has
                            no account assigned.""") %
                            (line.amount, line.partner_id.name))

                currency_id = order.mode.journal.currency and order.mode.journal.currency.id or company_currency_id

                if line.type == 'payable':
                    line_amount = line.amount_currency or line.amount
                else:
                    line_amount = -line.amount_currency or -line.amount

                if line_amount >= 0:
                    account_id = order.mode.journal.default_credit_account_id.id
                else:
                    account_id = order.mode.journal.default_debit_account_id.id
                acc_cur = ((line_amount <= 0) and order.mode.journal.default_debit_account_id) or line.account_id

                ctx = context.copy()
                ctx['res.currency.compute.account'] = acc_cur
                amount = currency_obj.compute(cr, uid, currency_id, company_currency_id, line_amount, context=ctx)

                val = {
                    'name': line.move_line_id and line.move_line_id.name or '/',
                    'move_id': move_id,
                    'date': order.date_done,
                    'ref': line.move_line_id and line.move_line_id.ref or False,
                    'partner_id': line.partner_id and line.partner_id.id or False,
                    'account_id': line.account_id.id,
                    'debit': ((amount > 0) and amount) or 0.0,
                    'credit': ((amount < 0) and - amount) or 0.0,
                    'journal_id': order.mode.journal.id,
                    'period_id': order.period_id.id,
                    'state': 'valid',
                }

                if currency_id <> company_currency_id:
                    amount_cur = currency_obj.compute(cr, uid, company_currency_id, currency_id, amount, context=ctx)
                    val['amount_currency'] = -amount_cur
                    val['currency_id'] = currency_id

                if line.account_id and line.account_id.currency_id and line.account_id.currency_id.id <> company_currency_id:
                    val['currency_id'] = line.account_id.currency_id.id
                    if company_currency_id == line.account_id.currency_id.id:
                        amount_cur = line_amount
                    else:
                        amount_cur = currency_obj.compute(cr, uid, company_currency_id, line.account_id.currency_id.id, amount, context=ctx)
                    val['amount_currency'] = amount_cur

                partner_line_id = move_line_obj.create(cr, uid, val, context, check=False)

                # Fill the secondary amount/currency
                # if currency is not the same than the company
                if currency_id <> company_currency_id:
                    amount_currency = line_amount
                    move_currency_id = currency_id
                else:
                    amount_currency = False
                    move_currency_id = False

                move_line_obj.create(cr, uid, {
                    'name': line.move_line_id and line.move_line_id.name or '/',
                    'move_id': move_id,
                    'date': order.date_done,
                    'ref': line.move_line_id and line.move_line_id.ref or False,
                    'partner_id': line.partner_id and line.partner_id.id or False,
                    'account_id': account_id,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'credit': ((amount > 0) and amount) or 0.0,
                    'journal_id': order.mode.journal.id,
                    'period_id': order.period_id.id,
                    'amount_currency': amount_currency,
                    'currency_id': move_currency_id,
                    'state': 'valid',
                }, context, check=False)

                if line.move_line_id and not line.move_line_id.reconcile_id:
                    # If payment line has a related move line, we try to reconcile it with the move we just created.
                    lines_to_reconcile = [
                        partner_line_id,
                    ]
                    # Check if payment line move is already partially reconciled and use those moves in that case.
                    if line.move_line_id.reconcile_partial_id:
                        for rline in line.move_line_id.reconcile_partial_id.line_partial_ids:
                            lines_to_reconcile.append( rline.id )
                    else:
                        lines_to_reconcile.append( line.move_line_id.id )
                    amount = 0.0
                    for rline in move_line_obj.browse(cr, uid, lines_to_reconcile, context):
                        amount += rline.debit - rline.credit

                    if currency_obj.is_zero(cr, uid, currency, amount):
                        move_line_obj.reconcile(cr, uid, lines_to_reconcile, 'payment', context=context)
                    else:
                        move_line_obj.reconcile_partial(cr, uid, lines_to_reconcile, 'payment', context)
                # Annotate the move id
                payment_line_obj.write(cr, uid, [line.id], {
                    'payment_move_id': move_id,
                }, context)
            # Post the move
            if order.mode.journal.entry_posted:
                move_obj.post(cr, uid, [move_id], context=context)

        return result


class payment_line(orm.Model):
    _inherit = 'payment.line'

    def _auto_init(self, cr, context=None):
        cr.execute("""SELECT column_name
            FROM
                information_schema.columns
            WHERE
                table_name = 'payment_line' and column_name='type'""")
        if cr.fetchone():
            update_sign = False
        else:
            update_sign = True
        result = super(payment_line, self)._auto_init(cr, context=context)

        if update_sign:
            # Ensure related store value of field 'type' is updated in
            # the database.
            # Note that by forcing the update here we also ensure
            # everything is done in the same transaction.
            # Because addons/__init__.py will execute a commit just
            # after creating table fields.
            result.sort()
            for item in result:
                item[1](cr, *item[2])
            # Change sign of 'receivable' payment lines
            cr.execute("""UPDATE payment_line
                SET
                    amount_currency = -amount_currency
                WHERE
                    type='receivable'""")
        return result

    _columns = {
        'move_line_id': fields.many2one(
            'account.move.line', 'Entry line',
            domain="[('reconcile_id', '=', False), ('amount_to_pay', '!=', 0), ('account_id.type', '=', parent.type), ('payment_type', 'ilike', parent.payment_type_name or '%')]",
             help="""This Entry Line will be referred for the information
                 of the ordering customer."""),
        'payment_move_id': fields.many2one(
            'account.move', 'Payment Move', readonly=True,
            help='Account move that pays this debt.'),
        'account_id': fields.many2one('account.account', 'Account'),
        'type': fields.related('order_id', 'type',
            type='selection', readonly=True, store=True, string='Type',
            selection=[('payable', 'Payable'), ('receivable', 'Receivable')]),
    }

    def onchange_move_line(self, cr, uid, ids, move_line_id, payment_type,
                        date_prefered, date_scheduled, currency=False,
                        company_currency=False, context=None):
        # Adds account.move.line name to the payment line communication
        result = super(payment_line, self).onchange_move_line(
            cr, uid, ids, move_line_id, payment_type, date_prefered,
            date_scheduled, currency, company_currency, context)
        if move_line_id:
            line = self.pool.get('account.move.line').browse(
                cr, uid, move_line_id, context=context)
            if line.name != '/':
                result['value']['communication'] = result['value']['communication'] + '. ' + line.name
            result['value']['account_id'] = line.account_id.id
            if context.get('order_id'):
                payment_order = self.pool.get('payment.order').browse(
                    cr, uid, context['order_id'], context=context)
                if payment_order.type == 'receivable':
                    result['value']['amount'] *= -1
                    result['value']['amount_currency'] *= -1
        return result
