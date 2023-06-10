# Copyright 2023 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def action_register_payment(self):
        """Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        """
        return {
            "name": _("Register Payment"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "context": {
                "active_model": "account.move.line",
                "active_ids": self.ids,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
