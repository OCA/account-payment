# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.tools import float_compare


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

        invoice = self.invoice_id
        if invoice and invoice.discount_due_date and invoice.has_discount:
            today = fields.Date.today()
            rounding = invoice.currency_id.rounding
            discount_amount = invoice.discount_amount
            pay_with_discount = (
                invoice.discount_due_date >= today and
                float_compare(
                    invoice.residual, invoice.amount_total,
                    precision_rounding=rounding,
                ) == 0
            )
            values['pay_with_discount'] = pay_with_discount
            if pay_with_discount:
                values['amount_currency'] -= discount_amount
        return values
