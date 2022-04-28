# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    customer_wallet_account_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.customer_wallet_account_id",
        readonly=True,
    )
    customer_wallet_balance = fields.Monetary(
        string="Customer Wallet Balance",
        compute="_compute_customer_wallet_balance",
        readonly=True,
    )

    def get_topmost_parent_id(self):
        if not self.parent_id:
            return self
        return self.parent_id.get_topmost_parent_id()

    def _compute_customer_wallet_balance(self):
        account_move_line = self.env["account.move.line"]
        if not self.ids:
            return True

        all_partners_in_family = {}
        all_partner_ids = set()
        all_account_ids = set()
        for partner in self:
            all_partners_in_family[partner] = (
                self.with_context(active_test=False)
                .search([("id", "child_of", partner.get_topmost_parent_id().id)])
                .ids
            )
            all_partner_ids |= set(all_partners_in_family[partner])
            all_account_ids.add(partner.customer_wallet_account_id.id)

        # generate where clause to include multicompany rules
        where_query = account_move_line._where_calc(
            [
                ("partner_id", "in", list(all_partner_ids)),
                # TODO: Filter on state?
                # ("state", "not in", ["draft", "cancel"]),
                # FIXME: This should ideally be something like
                # `("account_id", "=", partner.customer_wallet_account_id)`,
                # but that may not be possible.
                ("account_id", "in", list(all_account_ids)),
            ]
        )
        account_move_line._apply_ir_rules(where_query, "read")
        from_clause, where_clause, where_clause_params = where_query.get_sql()

        # balance is in the company currency
        query = (
            """
            SELECT SUM(balance) as total, partner_id
            FROM account_move_line account_move_line
            WHERE %s
            GROUP BY partner_id
            """
            % where_clause
        )
        self.env.cr.execute(query, where_clause_params)
        totals = self.env.cr.dictfetchall()
        for partner, child_ids in all_partners_in_family.items():
            partner.customer_wallet_balance = sum(
                -total["total"] for total in totals if total["partner_id"] in child_ids
            )
