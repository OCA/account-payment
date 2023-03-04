# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    check_date = fields.Date(
        default=fields.Date.context_today,
    )

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals["check_date"] = self.check_date or fields.Date.context_today(self)
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = super()._create_payment_vals_from_batch(batch_result)
        batch_values["check_date"] = self.check_date or fields.Date.context_today(self)
        return batch_values
