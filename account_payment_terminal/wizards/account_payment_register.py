# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):

    _name = "account.payment.register"
    _inherit = ["account.payment.register", "oca.payment.terminal.form.mixin"]

    need_payment_terminal = fields.Boolean(compute="_compute_need_payment_terminal")

    @api.depends("journal_id")
    def _compute_need_payment_terminal(self):
        for rec in self:
            if rec.journal_id.use_payment_terminal:
                rec.need_payment_terminal = True
            else:
                rec.need_payment_terminal = False

    @api.onchange("journal_id")
    def _unset_payment_terminal_on_journal_change(self):
        self.update({"account_payment_terminal_id": False})

    def get_payment_info(self):
        res = super().get_payment_info()
        res.update(
            {
                "amount": self.amount,
                "currency_iso": self.currency_id.name,
                "currency_decimals": self.currency_id.decimal_places,
                "payment_id": self.id,
                "order_id": self.communication,
            }
        )
        return res

    def action_confirm_payment(self, payment_reference):
        self.write({"communication": payment_reference})
        return self.action_create_payments()
