# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    @api.multi
    def _check_cash_discount_write_off_creation(self):
        self.ensure_one()
        return self.pay_with_discount

    @api.multi
    def get_cash_discount_writeoff_move_values(self):
        self.ensure_one()
        move_line = self.move_line_id
        partner = move_line.partner_id
        invoice = move_line.invoice_id
        company = invoice.company_id
        tax_adjustment = company.cash_discount_use_tax_adjustment

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
        supplier_account_amount = invoice.discount_amount
        discount_amount_credit = supplier_account_amount

        lines_values = list()
        lines_values.append({
            'partner_id': partner.id,
            'name': move_line_name,
            'debit': supplier_account_amount,
            'account_id': move_line.account_id.id,
        })

        if tax_adjustment:
            for tax_line in invoice.tax_line_ids:
                amount = tax_line.amount * invoice.discount_percent / 100.0
                discount_amount_credit -= amount
                lines_values.append({
                    'partner_id': partner.id,
                    'name': move_line_name,
                    'credit': amount,
                    'account_id': tax_line.account_id.id,
                    'tax_line_id': tax_line.tax_id.id,
                })

        lines_values.append({
            'partner_id': partner.id,
            'name': move_line_name,
            'credit': discount_amount_credit,
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
