# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _recompute_payment_terms_lines(self):
        _self = self
        if self.partner_id:
            _self = self.with_context(move_partner_id=self.partner_id.id)
        super(AccountMove, _self)._recompute_payment_terms_lines()
