# -*- coding: utf-8 -*-
# Copyright 2015 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    discount_due_date = fields.Date(
        related='invoice_id.discount_due_date',
        readonly=True,
    )
    discount_amount = fields.Monetary(
        related='invoice_id.discount_amount',
        readonly=True,
    )

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super(AccountMoveLine, self)._prepare_payment_line_vals(
            payment_order)

        values['original_amount_currency'] = values['amount_currency']
        invoice = self.invoice_id
        if invoice and invoice.discount_due_date:
            today = fields.Date.today()
            discount_amount = invoice.discount_amount
            amount_currency = abs(self.amount_residual) - discount_amount
            values.update({
                'pay_with_discount': invoice.discount_due_date >= today,
                'amount_currency': amount_currency,
                'discount_amount': discount_amount,
            })
        return values
