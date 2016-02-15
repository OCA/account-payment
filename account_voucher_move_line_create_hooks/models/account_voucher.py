# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2015 Ecosoft Pvt. Ltd. - Kitti Upariphutthiphong
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, models, _
from openerp.tools import float_compare
from openerp.exceptions import except_orm


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    @api.model
    def _voucher_move_line_prepare(self, voucher_id, line_total,
                                   move_id, company_currency, current_currency,
                                   voucher_line_id):

        voucher = self.env['account.voucher'].browse(voucher_id)
        line = self.env['account.voucher.line'].browse(voucher_line_id)
        return {
            'journal_id': voucher.journal_id.id,
            'period_id': voucher.period_id.id,
            'name': line.name or '/',
            'account_id': line.account_id.id,
            'move_id': move_id,
            'partner_id': voucher.partner_id.id,
            'currency_id': line.move_line_id and
            (company_currency != line.move_line_id.currency_id.id and
             line.move_line_id.currency_id.id) or False,
            'analytic_account_id': line.account_analytic_id and
            line.account_analytic_id.id or False,
            'quantity': 1,
            'credit': 0.0,
            'debit': 0.0,
            'date': voucher.date
        }

    @api.model
    def _voucher_move_line_foreign_currency_prepare(
            self, voucher_id, line_total, move_id,
            company_currency, current_currency, voucher_line_id,
            foreign_currency_diff):

        line = self.env['account.voucher.line'].browse(voucher_line_id)
        return {
            'journal_id': line.voucher_id.journal_id.id,
            'period_id': line.voucher_id.period_id.id,
            'name': _('change')+': '+(line.name or '/'),
            'account_id': line.account_id.id,
            'move_id': move_id,
            'partner_id': line.voucher_id.partner_id.id,
            'currency_id': line.move_line_id.currency_id.id,
            'amount_currency': -1 * foreign_currency_diff,
            'quantity': 1,
            'credit': 0.0,
            'debit': 0.0,
            'date': line.voucher_id.date,
        }

    @api.model
    def voucher_move_line_create(self, voucher_id, line_total,
                                 move_id, company_currency, current_currency):
        """
        This method replaces the original one in the account voucher module
        because it did not provide any hooks for customization.
        """
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        context = self._context
        # tax_obj = self.env['account.tax')  # used in v7 only
        tot_line = line_total
        rec_lst_ids = []
        date = self.browse(voucher_id).read(['date'])[0]['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.env['account.voucher'].browse(voucher_id)
        voucher_currency = voucher.journal_id.currency or \
            voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate *
            voucher.payment_rate,
            'voucher_special_currency': voucher.payment_rate_currency_id and
            voucher.payment_rate_currency_id.id or False, })
        prec = self.env['decimal.precision'].precision_get('Account')
        for line in voucher.line_ids:
            # create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line
            # was not having debit = credit = 0 (which is a legal value)
            if (
                not line.amount and
                not (line.move_line_id and
                     not float_compare(line.move_line_id.debit,
                                       line.move_line_id.credit,
                                       precision_digits=prec) and
                     not float_compare(line.move_line_id.debit, 0.0,
                                       precision_digits=prec))
            ):
                continue
            # convert the amount set on the voucher line into the
            # currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is
            # relevant or will use the default behaviour
            amount = self.with_context(ctx)._convert_amount(
                line.untax_amount or line.amount, voucher.id)
            # if the amount encoded in voucher is equal to the amount
            # unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise except_orm(
                        _('Wrong voucher line'),
                        _("The invoice you are willing to pay "
                          "is not valid anymore."))
                sign = line.type == 'dr' and -1 or 1
                currency_rate_difference = sign * (
                    line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            # hook
            move_line = self._voucher_move_line_prepare(
                voucher_id, line_total, move_id,
                company_currency, current_currency, line.id)
            # --
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type == 'dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the
                # original line had a foreign currency
                if line.move_line_id.currency_id and \
                        line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same
                        # currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 \
                            and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be
                        # used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = \
                            currency_obj.with_context(ctx).compute(
                                company_currency,
                                line.move_line_id.currency_id.id,
                                move_line['debit']-move_line['credit'])
                if line.amount == line.amount_unreconciled:
                    foreign_currency_diff = \
                        line.move_line_id.amount_residual_currency - abs(
                            amount_currency)

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(move_line)
            rec_ids = [voucher_line.id, line.move_line_id.id]

            if not voucher.company_id.currency_id.is_zero(
                    currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(
                    line, move_id, currency_rate_difference,
                    company_currency, current_currency)
                new = move_line_obj.create(exch_lines[0])
                move_line_obj.create(exch_lines[1])
                rec_ids.append(new.id)

            if line.move_line_id and line.move_line_id.currency_id and \
                    not line.move_line_id.currency_id.is_zero(
                        foreign_currency_diff):
                # Change difference entry in voucher currency
                # hook
                move_line_foreign_currency = \
                    self._voucher_move_line_foreign_currency_prepare(
                        voucher_id, line_total, move_id,
                        company_currency, current_currency, line.id,
                        foreign_currency_diff)
                # --
                new = move_line_obj.create(move_line_foreign_currency)
                rec_ids.append(new.id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        return tot_line, rec_lst_ids
