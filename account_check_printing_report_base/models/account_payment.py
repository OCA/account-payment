# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# (http://www.eficent.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 iterativo.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def do_print_checks(self):

        for rec in self:

            if rec.journal_id.check_layout_id:
                return (
                    self.env["ir.actions.report"]
                    ._get_report_from_name(rec.journal_id.check_layout_id.report)
                    .report_action(self)
                )

            elif rec.company_id.check_layout_id:
                return (
                    self.env["ir.actions.report"]
                    ._get_report_from_name(rec.company_id.check_layout_id.report)
                    .report_action(self)
                )

        return super(AccountPayment, self).do_print_checks()

    def post(self):
        res = super(AccountPayment, self).post()
        recs = self.filtered(
            lambda x: x.journal_id.check_print_auto
            and x.payment_method_id.code == "check_printing"
        )
        if recs:
            return recs.do_print_checks()
        return res
