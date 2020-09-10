# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaymentReturnLine(models.Model):
    _inherit = "payment.return.line"

    def _find_match(self):
        AccountMoveLine = self.env["account.move.line"]
        lines = self.filtered(lambda x: not x.move_line_ids and x.reference)
        for line in lines:
            line.move_line_ids = AccountMoveLine.search(
                [("bank_payment_line_id.name", "=", line.reference)]
            )
        return super(PaymentReturnLine, lines)._find_match()
