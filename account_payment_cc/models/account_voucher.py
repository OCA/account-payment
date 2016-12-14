# -*- coding: utf-8 -*-

from openerp import api, models


class AccountVoucher(models.Model):

    _inherit = 'account.voucher'

    @api.multi
    def action_move_line_create(self):
        res = super(AccountVoucher, self).action_move_line_create()

        move_line_pool = self.env['account.move.line']
        move_pool = self.env['account.move']

        for voucher in self:
            if voucher.journal_id.support_creditcard_transactions:
                company_currency = self._get_company_currency(voucher.id)
                current_currency = self._get_current_currency(voucher.id)

                partner_id = voucher.journal_id.partner_id
                account_payable = voucher.journal_id.partner_id.property_account_payable  # noqa
                account_receivable = voucher.journal_id.partner_id.property_account_receivable  # noqa
                account = voucher.journal_id.default_credit_account_id
                if voucher.type in ('receipt', 'sale'):
                    account = voucher.journal_id.default_debit_account_id
                # Create the account move record.
                move_id = move_pool.create(self.account_move_get(voucher.id))

                fline = self.first_move_line_get(
                    voucher.id,
                    move_id.id,
                    company_currency,
                    current_currency
                )

                fline.update({
                    'partner_id': partner_id and partner_id.id or
                    voucher.partner_id.id,
                })
                credit, debit = fline.get('credit'), fline.get('debit')
                alines = [line.id for line in voucher.line_ids if line.amount]
                ctx = {'date': voucher.date}
                if alines:
                    for line in voucher.line_ids:
                        # create one move line per voucher line where amount is
                        # not 0.0
                        if not line.amount:
                            continue
                        amount = abs(self.with_context(ctx)._convert_amount(
                            line.amount, voucher.id))
                        line_debit = line_credit = 0.0
                        if voucher.type in ('purchase', 'payment'):
                            line_credit = amount
                            line_debit = 0
                        elif voucher.type in ('sale', 'receipt'):
                            line_credit = 0
                            line_debit = amount

                        move_line = {
                            'journal_id': voucher.journal_id.id,
                            'period_id': voucher.period_id.id,
                            'name': line.name or '/',
                            'account_id': account_payable.id,
                            'move_id': move_id.id,
                            'partner_id': partner_id and partner_id.id or voucher.partner_id.id,  # noqa
                            'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,  # noqa
                            'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,  # noqa
                            'quantity': 1,
                            'credit': credit,
                            'debit': debit,
                            'date': voucher.date
                        }
                        if voucher.type in ('payment', 'purchase'):
                            move_line.update({'account_id':
                                              account_payable.id})
                            if line.type == 'cr':
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
                            if line.type == 'cr':
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

                        move_line_pool.create(move_line)
                else:
                    amount = self.with_context(ctx)._convert_amount(
                        (credit + debit), voucher.id)
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
                        'move_id': move_id.id,
                        'partner_id': partner_id and partner_id.id or
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
                    move_line_pool.create(move_line)
                move_line_pool.create(fline)
        return res

    @api.multi
    def cancel_voucher(self):
        move_pool = self.env['account.move']

        for voucher in self:
            voucher_number = voucher.number

            reconcile = self.env['account.move.reconcile']
            for line in voucher.move_ids:
                if line.reconcile_id:
                    reconcile += line.reconcile_id
                if line.reconcile_partial_id:
                    reconcile += line.reconcile_partial_id
            reconcile.unlink()

            if voucher.move_id:
                voucher.move_id.button_cancel()
                voucher.move_id.unlink()

            if voucher_number and\
                    voucher.journal_id.support_creditcard_transactions:
                cc_move = move_pool.search([("name", "=", voucher_number)])
                for move in cc_move:
                    if move.journal_id.support_creditcard_transactions:

                        reconcile = self.env['account.move.reconcile']
                        for line in move.line_id:
                            if line.reconcile_id:
                                reconcile += line.reconcile_id
                            if line.reconcile_partial_id:
                                reconcile += line.reconcile_partial_id
                        reconcile.unlink()

                        move.button_cancel()
                        move.unlink()

        res = {
            'state': 'cancel',
            'move_id': False,
        }
        self.write(res)
        return True
