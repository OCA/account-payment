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


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def do_print_checks(self):
        for rec in self:
            if rec.journal_id.bank_check_printing_layout:
                report_action = self.env.ref(
                    rec.journal_id.bank_check_printing_layout, False
                )
                self.write({"is_sent": True})
                return report_action.report_action(self)
        return super().do_print_checks()

    def action_post(self):
        res = super().action_post()
        recs = self.filtered(
            lambda x: x.journal_id.check_print_auto
            and x.payment_method_line_id.code == "check_printing"
        )
        if recs:
            return recs.do_print_checks()
        return res
