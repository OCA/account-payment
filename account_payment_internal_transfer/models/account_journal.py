# Copyright 2026 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def create_internal_transfer(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_account_payments"
        )
        action.update(
            {
                "views": [[False, "form"]],
                "context": {
                    "default_journal_id": self.id,
                    "default_payment_type": "outbound",
                    "default_is_internal_transfer": True,
                },
            }
        )
        return action
