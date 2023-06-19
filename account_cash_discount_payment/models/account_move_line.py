# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super()._prepare_payment_line_vals(payment_order)

        if self.discount_date and self.discount_percentage:
            today = fields.Date.today()
            pay_with_discount = self.discount_date >= today
            values["pay_with_discount"] = pay_with_discount
            if pay_with_discount:

                # compute discount amount
                if self.currency_id:
                    base_amount = self.amount_residual_currency
                else:
                    base_amount = self.amount_residual

                if self.move_id.is_invoice():
                    amount_with_discount = base_amount * -1
                # apply discount
                amount_with_discount *= 1 - (self.discount_percentage / 100)

                values["amount_currency"] = amount_with_discount
                # update discount_amount_currency on aml
                self.discount_amount_currency = self.amount_currency - (
                    base_amount + amount_with_discount
                )
                self.discount_balance = self.balance - (
                    base_amount + amount_with_discount
                )
        return values
