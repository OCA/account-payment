# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import float_compare


class AccountMove(models.Model):

    _inherit = "account.move"

    def _can_pay_invoice_with_discount(self, check_due_date=True):
        self.ensure_one()
        today = fields.Date.today()
        rounding = self.currency_id.rounding
        if not self.has_discount:
            return False

        if check_due_date:
            date_check_valid = self.discount_due_date >= today
        else:
            date_check_valid = True

        refunds_amount_total = self._get_refunds_amount_total()["total"]
        return (
            date_check_valid
            and float_compare(
                self.amount_residual,
                self.amount_total - refunds_amount_total,
                precision_rounding=rounding,
            )
            == 0
        )
