# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _seek_for_lines(self):
        # additionally filter writeoff lines to exclude tax line othervise
        # check defined _synchronize_from_moves will not pass
        liquidity_lines, counterpart_lines, writeoff_lines = super()._seek_for_lines()

        writeoff_lines = writeoff_lines.filtered(lambda l: not l.tax_line_id)
        return liquidity_lines, counterpart_lines, writeoff_lines
