# Copyright 2016 ForgeFLow, S.L.
# (http://www.forgeflow.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 iterativo.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        res = super().action_create_payments()
        if (
            self.journal_id.check_print_auto
            and self.payment_method_line_id.code == "check_printing"
        ):
            payment = self.env["account.payment"].search(
                [
                    ("journal_id", "=", self.journal_id.id),
                    (
                        "payment_method_line_id.name",
                        "like",
                        self.payment_method_line_id.name,
                    ),
                ],
                order="id desc",
                limit=1,
            )
            return payment.do_print_checks()
        return res
