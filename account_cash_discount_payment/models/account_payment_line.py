# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    pay_with_discount = fields.Boolean(
        default=False,
    )
    discount_due_date = fields.Date(
        related='move_line_id.invoice_id.discount_due_date',
        readonly=True,
    )
    discount_amount = fields.Monetary(
        related='move_line_id.invoice_id.discount_amount',
        readonly=True,
    )

    @api.multi
    @api.constrains(
        'pay_with_discount',
        'move_line_id',
    )
    def _check_pay_with_discount(self):
        for rec in self:
            if not rec.pay_with_discount:
                continue
            move_line = rec.move_line_id
            invoice = move_line and move_line.invoice_id or False
            if not invoice or not invoice.has_discount:
                raise ValidationError(
                    _("You can't pay with a discount if the payment line is "
                      "not linked to an invoice which has a discount."))

    @api.onchange(
        'discount_amount',
        'move_line_id',
        'pay_with_discount',
    )
    def _onchange_pay_with_discount(self):
        """
        This onchange should be executed completely only when the payment line
        is linked to a move line which is linked to an invoice which has a
        discount.

        If the above condition is ok, the amount will change based on the
        invoice total and invoice discount amount.
        """
        self._check_pay_with_discount()
        invoice = self.move_line_id.invoice_id
        if self.pay_with_discount:
            self.amount_currency = invoice.amount_total_with_discount
        else:
            self.amount_currency = invoice.amount_total
