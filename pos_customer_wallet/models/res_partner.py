# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    def _compute_customer_wallet_balance(self):
        super()._compute_customer_wallet_balance()
        for partner in self:
            statement_lines = self.env["account.bank.statement.line"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("state", "=", "open"),
                    ("statement_id.journal_id.is_customer_wallet_journal", "=", True),
                ]
            )
            partner.customer_wallet_balance += sum(
                -line.amount for line in statement_lines
            )

            # This is needed by pos_refresh_customer.
            partner.write({"write_date": fields.Datetime.now()})
