# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super()._prepare_payment_line_vals(payment_order)

        if self.discount_date and self.discount_amount_currency:
            today = fields.Date.today()
            pay_with_discount = self.discount_date >= today
            values["pay_with_discount"] = pay_with_discount
            if pay_with_discount:
                # apply discount
                values["amount_currency"] = self.discount_amount_currency * -1
        return values
