# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

DISCOUNT_ALLOWED_TYPES = (
    "in_invoice",
    "in_refund",
    "out_invoice",
)


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    origin_discount_amount_currency = fields.Monetary(
        string="Original Discount amount in Currency",
        currency_field="currency_id",
    )

    origin_discount_balance = fields.Monetary(
        string="Original Discount Balance",
        currency_field="company_currency_id",
    )

    discount_updated = fields.Boolean()

    def _prepare_discount(self):
        # compute discount amount
        amount_residual = self.amount_residual_currency

        if self.move_id.is_invoice():
            amount_residual *= -1
        # apply discount
        discount_amount_currency = (
            self.discount_amount_currency
            if not self.discount_updated
            else self.origin_discount_amount_currency
        )
        discount = abs(self.amount_currency) - abs(discount_amount_currency)
        refund_discount_amount = self.move_id._get_refunds_amount_total()["discount"]
        amount_with_discount = amount_residual - discount + refund_discount_amount
        # update discount_amount_currency on aml
        if not self.discount_updated:
            self.discount_updated = True
            self.origin_discount_amount_currency = self.discount_amount_currency
            self.origin_discount_balance = self.discount_balance
        self.discount_amount_currency = (
            self.origin_discount_amount_currency - refund_discount_amount
        )
        self.discount_balance = self.origin_discount_balance - refund_discount_amount
        return amount_with_discount

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super()._prepare_payment_line_vals(payment_order)

        if self.discount_date and self.discount_percentage:
            today = fields.Date.today()
            pay_with_discount = self.discount_date >= today
            values["pay_with_discount"] = pay_with_discount
            if pay_with_discount:
                values["amount_currency"] = self._prepare_discount()
        return values
