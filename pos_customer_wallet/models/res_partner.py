# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    statement_line_ids = fields.One2many(
        comodel_name="account.bank.statement.line", inverse_name="partner_id"
    )

    @api.depends(
        "customer_wallet_account_id",
        "customer_wallet_account_id.move_line_ids",
        "customer_wallet_account_id.move_line_ids.balance",
        "statement_line_ids",
        "statement_line_ids.amount",
        "statement_line_ids.state",
        "statement_line_ids.statement_id.journal_id.is_customer_wallet_journal",
    )
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
