# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2012-2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
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

from openerp.osv import fields, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class AccountVoucher(orm.Model):
    _inherit = "account.voucher"

    _columns = {
        'line_total': fields.float(
            'Lines Total', digits_compute=dp.get_precision('Account'),
            readonly=True),
        # exclude_write_off field will be used by modules like
        # account_vat_on_payment and l10n_it_withholding_tax
        'exclude_write_off': fields.boolean(
            'Exclude write-off from tax on payment',
            help="""Select this if you want, when closing the invoice, the
            tax to be computed
            based on the invoice's totals instead of the paid amount"""),
    }

    def balance_move(self, cr, uid, move_id, context=None):
        currency_obj = self.pool.get('res.currency')
        move = self.pool.get('account.move').browse(cr, uid, move_id, context)
        amount = 0.0
        for line in move.line_id:
            amount += line.debit - line.credit
        amount = currency_obj.round(
            cr, uid, move.company_id.currency_id, amount)
        # max_balance_diff improve the evaluation, beetwen
        # procedure's' error and an currency rounding's error
        max_balance_diff = move.company_id.max_balance_diff
        balance_diff = abs(amount * 10 ** dp.get_precision('Account')(cr)[1])
        # check if balance differs for more than 1 decimal according to account
        # decimal precision
        if (balance_diff > max_balance_diff):
            raise orm.except_orm(
                _('Error'),
                _(
                    'The generated payment entry '
                    'is unbalanced for more than %d '
                    'decimal' % max_balance_diff
                )
            )
        if not currency_obj.is_zero(
            cr, uid, move.company_id.currency_id, amount
        ):
            for line in move.line_id:
                # adjust the first move line that's not receivable, payable or
                # liquidity
                if (
                    line.account_id.type != 'receivable' and
                    line.account_id.type != 'payable' and
                    line.account_id.type != 'liquidity'
                ):
                    if line.credit:
                        line.write({
                            'credit': line.credit + amount,
                        }, update_check=False)
                    elif line.debit:
                        line.write({
                            'debit': line.debit - amount,
                        }, update_check=False)
                    if line.tax_amount:
                        line.write({
                            'tax_amount': line.tax_amount + amount,
                        }, update_check=False)
                    break
        return amount

    def voucher_move_line_create(
        self, cr, uid, voucher_id, line_total,
        move_id, company_currency, current_currency, context=None
    ):
        res = super(AccountVoucher, self).voucher_move_line_create(
            cr, uid, voucher_id, line_total, move_id, company_currency,
            current_currency, context)
        self.write(cr, uid, voucher_id, {'line_total': res[0]}, context)
        return res

    def get_invoice_total(self, invoice):
        res = 0.0
        for inv_move_line in invoice.move_id.line_id:
            if inv_move_line.account_id.type in ('receivable', 'payable'):
                res += inv_move_line.debit or inv_move_line.credit
        return res

    def get_invoice_total_currency(self, invoice):
        res = 0.0
        for inv_move_line in invoice.move_id.line_id:
            if inv_move_line.account_id.type in ('receivable', 'payable'):
                res += abs(inv_move_line.amount_currency)
        return res

    def allocated_amounts_grouped_by_invoice(
        self, cr, uid, voucher, context=None
    ):
        '''

        this method builds a dictionary in the following form

        {
            first_invoice_id: {
                'allocated': 120.0,
                'total': 120.0,
                'total_currency': 0.0,
                'write-off': -20.0,
                'allocated_currency': 0.0,
                'foreign_currency_id': False, # int
                'currency-write-off': 0.0,
                }
            second_invoice_id: {
                'allocated': 50.0,
                'total': 100.0,
                'total_currency': 0.0,
                'write-off': 0.0,
                'allocated_currency': 0.0,
                'foreign_currency_id': False,
                'currency-write-off': 0.0,
                }
        }

        every amout is expressed in company currency.

        In order to compute cashed amount correctly, write-off will be
        subtract to reconciled amount.
        If more than one invoice is paid with this voucher, we distribute
        write-off equally (if allowed)

        '''
        res = {}
        ctx = dict(context) or {}
        company_currency = super(AccountVoucher, self)._get_company_currency(
            cr, uid, voucher.id, context=ctx)
        current_currency = super(AccountVoucher, self)._get_current_currency(
            cr, uid, voucher.id, context=ctx)
        for line in voucher.line_ids:
            if line.amount and line.move_line_id and line.move_line_id.invoice:
                if line.move_line_id.invoice.id not in res:
                    res[line.move_line_id.invoice.id] = {
                        'allocated': 0.0,
                        'total': 0.0,
                        'total_currency': 0.0,
                        'write-off': 0.0,
                        'allocated_currency': 0.0,
                        'foreign_currency_id': False,
                        'currency-write-off': 0.0,
                    }
                current_amount = line.amount
                if company_currency != current_currency:
                    ctx['date'] = voucher.date
                    current_amount = super(
                        AccountVoucher, self)._convert_amount(
                            cr, uid, line.amount, voucher.id, context=ctx)
                    res[line.move_line_id.invoice.id][
                        'allocated_currency'
                    ] += line.amount
                    res[line.move_line_id.invoice.id][
                        'foreign_currency_id'
                    ] = current_currency
                    res[line.move_line_id.invoice.id][
                        'total_currency'
                    ] = self.get_invoice_total_currency(
                        line.move_line_id.invoice)
                res[line.move_line_id.invoice.id][
                    'allocated'
                ] += current_amount
                res[line.move_line_id.invoice.id][
                    'total'
                ] = self.get_invoice_total(line.move_line_id.invoice)
        if res:
            # we use line_total as it can be != writeoff_amount in case of
            # multi currency
            write_off_per_invoice = voucher.line_total / len(res)
            if not voucher.company_id.allow_distributing_write_off and len(
                res
            ) > 1 and write_off_per_invoice:
                raise orm.except_orm(_('Error'), _(
                    'You are trying to pay with write-off more than one '
                    'invoice and distributing write-off is not allowed. '
                    'See company settings.'))
            if voucher.type == 'payment' or voucher.type == 'purchase':
                write_off_per_invoice = - write_off_per_invoice
            for inv_id in res:
                res[inv_id]['write-off'] = write_off_per_invoice
            if company_currency != current_currency:
                curr_write_off_per_invoice = voucher.writeoff_amount / len(res)
                if voucher.type == 'payment' or voucher.type == 'purchase':
                    curr_write_off_per_invoice = - curr_write_off_per_invoice
                for inv_id in res:
                    res[inv_id][
                        'currency-write-off'] = curr_write_off_per_invoice
        return res
