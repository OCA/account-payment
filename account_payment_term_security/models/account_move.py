# Copyright 2023-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_account_payment_term_mgmt = fields.Boolean(
        compute="_compute_is_account_payment_term_mgmt", store=False
    )

    def _compute_is_account_payment_term_mgmt(self):
        for rec in self:
            rec.is_account_payment_term_mgmt = self.env.user.has_group(
                "account_payment_term_security.account_payment_term_mgmt"
            )
