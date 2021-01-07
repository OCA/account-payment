# Copyright 2021 Tecnativa Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _recompute_payment_terms_lines(self):
        super(
            AccountMove, self.with_context(last_account_move=self)
        )._recompute_payment_terms_lines()
