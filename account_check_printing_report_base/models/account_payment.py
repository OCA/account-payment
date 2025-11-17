# Copyright 2016 ForgeFLow, S.L.
# (http://www.forgeflow.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 iterativo.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


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
