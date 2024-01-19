# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _get_amount_after_discount(self):
        percentage = 1 - (self.discount_percentage / 100.0)
        amount_residual = (
            self.amount_residual - self.move_id._get_refunds_amount_total()
        )

        if self.move_id.is_invoice():
            amount_residual *= -1

        amount_after_discount = self.currency_id.round(amount_residual * percentage)
        discount_amount = amount_residual - amount_after_discount

        return amount_after_discount, discount_amount

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super()._prepare_payment_line_vals(payment_order)

        if self.discount_date and self.discount_percentage:
            today = fields.Date.today()
            pay_with_discount = self.discount_date >= today
            values["pay_with_discount"] = pay_with_discount
            if pay_with_discount:
                (
                    amount_after_discount,
                    discount_amount,
                ) = self._get_amount_after_discount()
                values["amount_currency"] = amount_after_discount
                # set discount_balance on aml
                # the difference between the balance and the
                # discount balance should be the "real amount"
                # because it wille be used to compute the Early
                # Payment Discount aml after payment by Odoo.
                # it is a bit of a hack because Odoo doesn't take into
                #   account any credit notes when computing the discount_amount
                if self.move_id.is_invoice():
                    discount_amount *= -1
                self.discount_balance = self.balance - discount_amount
                self.discount_amount_currency = self.amount_currency - discount_amount
        return values
