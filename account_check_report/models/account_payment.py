# 2016-2024 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models
from odoo.osv import expression


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends(
        "move_id.line_ids.matched_debit_ids", "move_id.line_ids.matched_credit_ids"
    )
    def _compute_stat_buttons_from_reconciliation(self):
        res = super()._compute_stat_buttons_from_reconciliation()
        for rec in self:
            if rec.payment_type == "outbound":
                open_action = rec.button_open_bills()
                result_domain = open_action.get("domain", False)
                if not result_domain:
                    return res
                rec.reconciled_bills_count = len(
                    self.env["account.move"].search(result_domain)
                )
            else:
                open_action = rec.button_open_invoices()
                result_domain = open_action.get("domain", False)
                if not result_domain:
                    return res
                rec.reconciled_invoices_count = len(
                    self.env["account.move"].search(result_domain)
                )
        return res

    def get_direct_refunds(self):
        if self.payment_type == "outbound":
            move_lines = self.reconciled_bill_ids.mapped("line_ids")
        else:
            move_lines = self.reconciled_invoice_ids.mapped("line_ids")
        rec_lines = move_lines.filtered(
            lambda x: x.account_id.reconcile
            and x.account_id == self.destination_account_id
            and x.partner_id == self.partner_id
        )
        # include direct refunds
        if self.partner_type == "customer":
            invoice_ids = rec_lines.mapped(
                "matched_credit_ids.credit_move_id.full_reconcile_id."
                "reconciled_line_ids.move_id"
            ).filtered(lambda i: i.date <= self.date)
        elif self.partner_type == "supplier":
            invoice_ids = rec_lines.mapped(
                "matched_debit_ids.debit_move_id.full_reconcile_id."
                "reconciled_line_ids.move_id"
            ).filtered(lambda i: i.date <= self.date)
        # include other invoices where the payment was applied
        invoice_ids += rec_lines.mapped(
            "matched_credit_ids.credit_move_id.move_id"
        ) + rec_lines.mapped("matched_debit_ids.debit_move_id.move_id")
        if not invoice_ids:
            return False
        invoice_ids -= self.move_id
        return invoice_ids

    def get_direct_refunds_domain(self):
        invoices = self.get_direct_refunds()
        if invoices:
            return [("id", "in", invoices.ids)]
        return []

    def button_open_invoices(self):
        res = super(AccountPayment, self).button_open_invoices()
        if not res.get("domain", False):
            return res
        result_domain = res.get("domain", False)
        direct_refunds_domain = self.get_direct_refunds_domain()
        if direct_refunds_domain:
            res["domain"] = expression.OR([result_domain, direct_refunds_domain])
        return res

    def button_open_bills(self):
        """
        Include direct refunds, those are not linked to the payments
        directly
        """
        res = super(AccountPayment, self).button_open_bills()
        if not res.get("domain", False):
            return res
        result_domain = res.get("domain", False)
        direct_refunds_domain = self.get_direct_refunds_domain()
        if direct_refunds_domain:
            res["domain"] = expression.OR([result_domain, direct_refunds_domain])
        return res
