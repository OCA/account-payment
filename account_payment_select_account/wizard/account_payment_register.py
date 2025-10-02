from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    payment_account_id = fields.Many2one("account.account", string="Account")
    require_payment_account = fields.Boolean(
        compute="_compute_require_payment_account",
    )

    @api.depends(
        "payment_method_line_id.payment_account_id",
    )
    def _compute_require_payment_account(self):
        for rec in self:
            rec.require_payment_account = (
                not rec.payment_method_line_id.payment_account_id
            )

    def _create_payment_vals_from_wizard(self, batch_result):
        res = super()._create_payment_vals_from_wizard(batch_result)
        if self.require_payment_account and self.payment_account_id:
            res["outstanding_account_id"] = self.payment_account_id.id
        return res
