# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _compute_customer_wallet_balance(self):
        super()._compute_customer_wallet_balance()

        account_bank_statement_line = self.env["account.bank.statement.line"]
        if not self.ids:
            return True

        all_partners_in_family = {}
        all_partner_ids = set()
        for partner in self:
            all_partners_in_family[partner] = (
                self.with_context(active_test=False)
                .search([("id", "child_of", partner.get_topmost_parent_id().id)])
                .ids
            )
            all_partner_ids |= set(all_partners_in_family[partner])

        # generate where clause to include multicompany rules
        where_query = account_bank_statement_line._where_calc(
            [
                ("partner_id", "in", list(all_partner_ids)),
                ("state", "=", "open"),
                ("statement_id.journal_id.is_customer_wallet_journal", "=", True),
            ]
        )
        account_bank_statement_line._apply_ir_rules(where_query, "read")
        from_clause, where_clause, where_clause_params = where_query.get_sql()

        # amount is in the company currency
        query = (
            """
            SELECT SUM(amount) as total, partner_id
            FROM account_bank_statement_line account_bank_statement_line
            WHERE %s
            GROUP BY partner_id
            """
            % where_clause
        )
        self.env.cr.execute(query, where_clause_params)
        totals = self.env.cr.dictfetchall()
        for partner, child_ids in all_partners_in_family.items():
            partner.customer_wallet_balance += sum(
                -total["total"] for total in totals if total["partner_id"] in child_ids
            )
