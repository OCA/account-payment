# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OcaPaymentTerminalFormMixin(models.AbstractModel):

    _name = "oca.payment.terminal.form.mixin"
    _description = "OCA Payment Terminal Form Mixin"

    account_payment_terminal_id = fields.Many2one(
        comodel_name="account.payment.terminal", string="Payment Terminal"
    )

    def action_payment_terminal_transaction_start(self):
        self.ensure_one()
        if not hasattr(self, "journal_id"):
            # the object must be linked to journal in order to get the payment
            # terminal type
            return {}
        if (
            self.journal_id.use_payment_terminal
            and self.account_payment_terminal_id
            and hasattr(
                self, self._get_payment_terminal_transaction_start_method_name()
            )
        ):
            return getattr(
                self, self._get_payment_terminal_transaction_start_method_name()
            )()
        raise UserError(
            _(
                "Payment terminal is not correctly configured. "
                "Please contact your administrator."
            )
        )

    def _get_payment_terminal_transaction_start_method_name(self):
        return "_%s_transaction_start" % self.journal_id.use_payment_terminal or ""

    def _oca_payment_terminal_transaction_start(self):
        self.ensure_one()
        view_id = self._get_payment_terminal_form_view_id()
        return {
            "name": _("Payment Terminal"),
            "type": "ir.actions.act_window",
            "view_mode": "oca_payment_terminal_form",
            "res_model": self._name,
            "res_id": self.id,
            "target": "new",
            "view_id": view_id,
            "context": self.env.context,
        }

    @api.model
    def _get_payment_terminal_form_view_id(self):
        return self.env.ref(
            "account_payment_terminal.oca_payment_terminal_form_mixin_form_view"
        ).id

    # To define in the heir model
    def get_payment_info(self):
        raise NotImplementedError()

    def action_confirm_payment(self, payment_reference):
        raise NotImplementedError()
