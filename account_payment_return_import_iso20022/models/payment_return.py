# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2020 Tecnativa - Víctor Martínez
# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaymentReturnLine(models.Model):
    _inherit = "payment.return.line"

    def _find_match(self):
        """Include in the matches the lines coming from payment orders."""
        matched = self.env["payment.return.line"]
        # noqa B023
        for line in self.filtered(lambda x: not x.move_line_ids and x.reference):
            move_id = int(line.reference) if line.reference.isdigit() else -1
            payments = self.env["account.payment"].search(
                [
                    ("move_id", "=", move_id),
                    ("payment_order_id", "!=", False),
                ],
            )
            if payments:
                line.partner_id = payments[0].partner_id
                matched += line
                for payment in payments:
                    line.move_line_ids |= payment.move_id.line_ids.filtered(
                        lambda x, payment=payment: x.account_id
                        == payment.destination_account_id
                        and x.partner_id == payment.partner_id
                    )
        return super(PaymentReturnLine, self - matched)._find_match()
