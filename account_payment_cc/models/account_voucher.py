# -*- coding: utf-8 -*-


from openerp.osv import osv


class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    def action_move_line_create(self, cr, uid, ids, context=None):
        res = super(account_voucher, self).action_move_line_create(cr, uid,
                                                                   ids,
                                                                   context)
        move_line_pool = self.pool.get('account.move.line')
        move_pool = self.pool.get('account.move')
        for voucher in self.browse(cr, uid, ids):
            if voucher.journal_id.support_creditcard_transactions:
                company_currency = self._get_company_currency(cr, uid,
                                                              voucher.id,
                                                              context)
                current_currency = self._get_current_currency(cr, uid,
                                                              voucher.id,
                                                              context)

                partner_id = voucher.journal_id.partner_id
                account_payable = voucher.journal_id.partner_id.property_account_payable  # noqa
                account_receivable = voucher.journal_id.partner_id.property_account_receivable  # noqa
                account = voucher.journal_id.default_credit_account_id
                if voucher.type in ('receipt', 'sale'):
                    account = voucher.journal_id.default_debit_account_id
                # Create the account move record.
                move_id = move_pool.create(cr, uid,
                                           self.account_move_get(cr, uid,
                                                                 voucher.id,
                                                                 context=
                                                                 context),
                                           context=context)
                
                fline = self.first_move_line_get(cr,uid,voucher.id, move_id,
                                                 company_currency,
                                                 current_currency, context)
                fline.update({
                    'partner_id': partner_id and partner_id.id or
                                  voucher.partner_id.id,
                })
                credit, debit = fline.get('credit'), fline.get('debit')
                alines = [line.id for line in voucher.line_ids if line.amount]
                ctx = context and context.copy() or {}
                ctx.update({'date': voucher.date})
                if alines:
                    for line in voucher.line_ids:
                        # create one move line per voucher line where amount is
                        # not 0.0
                        if not line.amount:
                            continue
                        amount = self._convert_amount(cr, uid, line.amount,
                                                      voucher.id, context=ctx)
                        line_debit = line_credit = 0.0
                        if voucher.type in ('purchase', 'payment'):
                            line_credit = amount
                        elif voucher.type in ('sale', 'receipt'):
                            line_debit = amount
                        if line_debit < 0:
                            line_credit = -line_debit
                        else:
                            line_debit = 0.0
                        if line_credit < 0:
                            line_debit = -line_credit
                        else:
                            line_credit = 0.0
                        move_line = {
                            'journal_id': voucher.journal_id.id,
                            'period_id': voucher.period_id.id,
                            'name': line.name or '/',
                            'account_id': account_payable.id,
                            'move_id': move_id,
                            'partner_id': partner_id and partner_id.id or voucher.partner_id.id, # noqa
                            'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False, # noqa
                            'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False, # noqa
                            'quantity': 1,
                            'credit': credit,
                            'debit': debit,
                            'date': voucher.date
                        }
                        if voucher.type in ('payment', 'purchase'):
                            move_line.update({'account_id':
                                                  account_payable.id})
                            if line.type=='cr':
                                move_line['debit'] = line_debit
                                fline.update({
                                    'credit': debit, 'debit': credit,
                                })
                            else:
                                move_line['credit'] = line_credit
                                fline.update({
                                    'credit': debit, 'debit': credit,
                                    'account_id': account.id
                                })
                        if voucher.type in ('receipt', 'sale'):
                            move_line.update({'account_id':
                                                  account_receivable.id})
                            if line.type=='cr':
                                fline.update({
                                    'credit': debit, 'debit': credit,
                                    'account_id': account.id
                                })
                                move_line['debit'] = line_debit
                            else:
                                move_line['credit'] = line_credit
                                fline.update({
                                    'credit': debit, 'debit': credit,
                                })
                        move_line_pool.create(cr, uid, move_line, context)
                else:
                    amount = self._convert_amount(cr, uid, (credit+debit),
                                                  voucher.id, context=ctx)
                    line_debit = line_credit = 0.0
                    if voucher.type in ('purchase', 'payment'):
                        line_credit = amount
                    elif voucher.type in ('sale', 'receipt'):
                        line_debit = amount
                    if line_debit < 0:
                        line_credit = -line_debit
                    else:
                        line_debit = 0.0
                    if line_credit < 0:
                        line_debit = -line_credit
                    else:
                        line_credit = 0.0
                    move_line = {
                        'journal_id': voucher.journal_id.id,
                        'period_id': voucher.period_id.id,
                        'name': voucher.name or '/',
                        'account_id': account_payable.id,
                        'move_id': move_id,
                        'partner_id': partner_id and partner_id.id or \
                                      voucher.partner_id.id,
                        'quantity': 1,
                        'credit': credit,
                        'debit': debit,
                        'date': voucher.date
                    }
                    if voucher.type in ('receipt', 'sale'):
                        move_line.update({'account_id': account_receivable.id})
                    if (credit > 0):
                        move_line['debit'] = amount
                    else:
                        move_line['credit'] = amount
                    move_line_pool.create(cr, uid, move_line, context)
                move_line_pool.create(cr, uid, fline, context)
        return res


    def cancel_voucher(self, cr, uid, ids, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')

        for voucher in self.browse(cr, uid, ids, context=context):
            voucher_number = voucher.number
            recs = []
            for line in voucher.move_ids:
                if line.reconcile_id:
                    recs += [line.reconcile_id.id]
                if line.reconcile_partial_id:
                    recs += [line.reconcile_partial_id.id]

            reconcile_pool.unlink(cr, uid, recs)

            if voucher.move_id:
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])

            if voucher_number and\
                    voucher.journal_id.support_creditcard_transactions:
                cc_move = move_pool.search(cr, uid,
                                           [("name", "=", voucher_number)],
                                           context=context)
                for move in move_pool.browse(cr, uid, cc_move,
                                             context=context):
                    if move.journal_id.support_creditcard_transactions:
                        recs = []
                        for line in move.line_id:
                            if line.reconcile_id:
                                recs += [line.reconcile_id.id]
                            if line.reconcile_partial_id:
                                recs += [line.reconcile_partial_id.id]
                        reconcile_pool.unlink(cr, uid, recs, context=context)
                        move_pool.button_cancel(cr, uid, [move.id],
                                                context=context)
                        move_pool.unlink(cr, uid, [move.id], context=context)

        res = {
            'state':'cancel',
            'move_id': False,
        }
        self.write(cr, uid, ids, res)
        return True
