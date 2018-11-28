# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    @api.multi
    def _check_cash_discount_write_off_creation(self):
        self.ensure_one()
        create_write_off = (
            self.pay_with_discount and
            self.move_line_id and
            self.move_line_id.invoice_id and
            self.move_line_id.invoice_id.has_discount
        )
        if not create_write_off:
            return False

        invoice = self.move_line_id.invoice_id
        refunds_amount_total = 0.0
        for pmove_line in invoice.payment_move_line_ids:
            pmove_line_inv = pmove_line.invoice_id
            if pmove_line_inv and pmove_line_inv.type == 'in_refund':
                refunds_amount_total += pmove_line_inv.amount_total

        # Invoice residual has already changed so we need to compute
        # the residual with discount before the first reconciliation
        amount_to_pay = (
            invoice.amount_total -
            refunds_amount_total -
            invoice.discount_amount +
            invoice.refunds_discount_amount
        )
        return float_compare(
            self.amount_currency,
            amount_to_pay,
            precision_rounding=self.currency_id.rounding
        ) == 0

    @api.multi
    def get_cash_discount_writeoff_move_values(self):
        self.ensure_one()
        move_line = self.move_line_id
        partner = move_line.partner_id
        invoice = move_line.invoice_id
        company = invoice.company_id
        tax_adjustment = company.cash_discount_use_tax_adjustment
        rounding = self.currency_id.rounding

        woff_account = False
        woff_journal = False

        if invoice:
            company = invoice.company_id
            woff_account = company.default_cash_discount_writeoff_account_id
            woff_journal = company.default_cash_discount_writeoff_journal_id

        if not woff_account or not woff_journal:
            raise UserError(
                _("You have to fill in journal and account for cash discount "
                  "write-off on the company.")
            )

        move_line_name = _("Cash Discount Write-Off")
        supplier_account_amount = (
            invoice.discount_amount -
            invoice.refunds_discount_amount
        )
        discount_amount_credit = supplier_account_amount

        lines_values = [{
            'partner_id': partner.id,
            'name': move_line_name,
            'debit': supplier_account_amount,
            'account_id': move_line.account_id.id,
        }]

        if tax_adjustment:
            refund_moves = invoice.payment_move_line_ids.filtered(
                lambda line: line.invoice_id.type == 'in_refund'
            ).mapped('move_id')
            target_move_ids = refund_moves.ids + [move_line.move_id.id]

            tax_move_lines = self.env['account.move.line'].search([
                ('move_id', 'in', target_move_ids),
                '|',
                ('tax_line_id', '!=', False),
                ('tax_ids', '!=', False)
            ])

            for tax_move_line in tax_move_lines:
                tax_invoice = tax_move_line.invoice_id
                amount = float_round(
                    abs(tax_move_line.balance) *
                    tax_invoice.discount_percent / 100.0,
                    precision_rounding=rounding,
                )
                if tax_move_line.credit > 0:
                    discount_amount_credit += amount
                elif tax_move_line.debit > 0:
                    discount_amount_credit -= amount

                if tax_move_line.tax_line_id:
                    account = tax_move_line.account_id
                else:
                    account = woff_account
                lines_values.append({
                    'partner_id': partner.id,
                    'name': move_line_name,
                    'debit': tax_move_line.credit > 0 and amount or 0.0,
                    'credit': tax_move_line.debit > 0 and amount or 0.0,
                    'account_id': account.id,
                    'tax_line_id': tax_move_line.tax_line_id.id,
                    'tax_ids': [(6, 0, tax_move_line.tax_ids.ids)]
                })

        amount_left = not float_is_zero(
            discount_amount_credit,
            precision_rounding=rounding
        )
        if amount_left:
            writeoff_amount = float_round(
                abs(discount_amount_credit),
                precision_rounding=rounding,
            )
            lines_values.append({
                'partner_id': partner.id,
                'name': move_line_name,
                'credit': (
                    writeoff_amount
                    if discount_amount_credit > 0
                    else 0.0
                ),
                'debit': (
                    writeoff_amount
                    if discount_amount_credit < 0
                    else 0.0
                ),
                'account_id': woff_account.id,
            })

        move_values = {
            'journal_id': woff_journal.id,
            'partner_id': partner.id,
            'line_ids': [
                (0, 0, values)
                for values in lines_values
            ]
        }
        return move_values
