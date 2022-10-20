# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    payment_method_code = fields.Char(related="payment_method_id.code")
    check_payee = fields.Char(
        string="Payee",
        compute="_compute_check_payee",
        required=True,
        readonly=False,
        copy=False,
        store=True,
    )

    @api.depends("partner_id", "payment_method_code")
    def _compute_check_payee(self):
        for rec in self:
            rec.check_payee = rec.partner_id.name or "-"

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals["check_payee"] = self.check_payee or "-"
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = super()._create_payment_vals_from_batch(batch_result)
        batch_values["check_payee"] = self.check_payee or "-"
        return batch_values
