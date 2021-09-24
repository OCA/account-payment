# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    discount_due_date = fields.Date(
        related="move_id.discount_due_date",
        readonly=True,
    )
    discount_amount = fields.Monetary(
        related="move_id.discount_amount",
        readonly=True,
    )

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super(AccountMoveLine, self)._prepare_payment_line_vals(payment_order)

        move = self.move_id
        if move and move.discount_due_date and move.has_discount:
            pay_with_discount = move._can_pay_invoice_with_discount()
            values["pay_with_discount"] = pay_with_discount
            if pay_with_discount:
                values["amount_currency"] = move.residual_with_discount
        return values
