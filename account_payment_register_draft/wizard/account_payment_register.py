# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

MAPPING_TYPE = {
    "inbound": "register_customer_payment_state",
    "outbound": "register_vendor_payment_state",
}


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _check_payment_draft(self):
        return bool(self.env.company[MAPPING_TYPE.get(self.payment_type)] == "draft")

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        if self._check_payment_draft():
            payment_vals["to_auto_reconcile"] = self._get_batches()[0]["lines"]
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        if self._check_payment_draft():
            payment_vals["to_auto_reconcile"] = batch_result["lines"]
        return payment_vals

    def _create_payments(self):
        self = self.with_context(skip_clear_auto_reconcile=1)
        payments = super()._create_payments()
        if self._check_payment_draft():
            payments.with_context(skip_clear_auto_reconcile=1).action_draft()
        return payments
