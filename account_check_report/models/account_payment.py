# -*- coding: utf-8 -*-
# 2016-2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models
from odoo.osv import expression


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def get_direct_refunds(self):
        rec_lines = self.move_line_ids.filtered(
            lambda x: x.account_id.reconcile
            and x.account_id == self.destination_account_id
            and x.partner_id == self.partner_id
        )
        # include direct refunds
        if self.partner_type == "customer":
            invoice_ids = rec_lines.mapped(
                "matched_debit_ids.debit_move_id.matched_credit_ids."
                "credit_move_id.invoice_id"
            ).filtered(lambda i: i.date_invoice <= self.payment_date)
        elif self.partner_type == "supplier":
            invoice_ids = rec_lines.mapped(
                "matched_credit_ids.credit_move_id.matched_debit_ids."
                "debit_move_id.invoice_id"
            ).filtered(lambda i: i.date_invoice <= self.payment_date)
        # include other invoices where the payment was applied
        invoice_ids += rec_lines.mapped(
            "matched_credit_ids.credit_move_id.invoice_id"
        ) + rec_lines.mapped("matched_debit_ids.debit_move_id.invoice_id")
        if not invoice_ids:
            return False
        return [("id", "in", invoice_ids.ids)]

    @api.multi
    def button_invoices(self):
        """
        Include direct refunds, those are not linked to the payments
        directly
        """
        res = super(AccountPayment, self).button_invoices()
        if not res.get("domain", False):
            return res
        result_domain = res.get("domain", False)
        direct_refunds_domain = self.get_direct_refunds()
        if direct_refunds_domain:
            res["domain"] = expression.OR(
                [result_domain, direct_refunds_domain]
            )
        return res
