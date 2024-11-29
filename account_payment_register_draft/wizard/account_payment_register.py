# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals["to_auto_reconcile"] = self._get_batches()[0]["lines"]
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        payment_vals["to_auto_reconcile"] = batch_result["lines"]
        return payment_vals

    def _create_payments(self):
        self = self.with_context(skip_clear_auto_reconcile=1)
        payments = super()._create_payments()
        mapping_function = {
            "inbound": "register_customer_payment_state",
            "outbound": "register_vendor_payment_state",
        }
        if (
            mapping_function.get(self.payment_type, False)
            and self.env.company[mapping_function[self.payment_type]] == "draft"
        ):
            payments.with_context(skip_clear_auto_reconcile=1).action_draft()
        return payments
