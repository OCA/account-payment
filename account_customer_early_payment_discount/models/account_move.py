# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import timedelta

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    early_payment_state = fields.Selection(
        [("available", "To Apply"), ("applied", "Applied")],
        compute="_compute_early_payment_state",
        store=True,
        help="To Apply: the customer paid in time and the credit note is not "
        "issued yet. Applied: the credit note is issued.",
    )

    @api.depends(
        "invoice_payment_term_id.early_discount",
        "invoice_payment_term_id.early_discount_credit_note",
        "invoice_payment_term_id.early_discount_business_days",
        "invoice_payment_term_id.early_discount_goods_only",
        "invoice_payment_term_id.discount_percentage",
        "invoice_payment_term_id.discount_days",
        "invoice_line_ids.price_total",
        "invoice_line_ids.product_id.type",
    )
    def _compute_early_payment(self):
        return super()._compute_early_payment()

    @api.depends(
        "state",
        "early_payment_date",
        "early_payment_amount",
        "early_payment_credit_note_id.state",
        "amount_residual",
    )
    def _compute_early_payment_state(self):
        for move in self:
            credit_note = move.early_payment_credit_note_id
            if credit_note and credit_note.state != "cancel":
                move.early_payment_state = "applied"
            elif (
                move.state == "posted"
                and move.early_payment_date
                and move.early_payment_amount > 0
                and move._early_payment_paid_on_time()
            ):
                move.early_payment_state = "available"
            else:
                move.early_payment_state = False

    @api.depends("early_payment_state")
    def _compute_early_payment_can_apply(self):
        return super()._compute_early_payment_can_apply()

    def _get_early_payment_values(self):
        values = super()._get_early_payment_values()
        term = self.invoice_payment_term_id
        if not (
            self.move_type == "out_invoice"
            and self.invoice_date
            and term.early_discount
            and term.early_discount_credit_note
        ):
            return values
        base = sum(self._early_payment_eligible_lines().mapped("price_total"))
        return {
            "date": (
                self.company_id._add_business_days(
                    self.invoice_date, term.discount_days
                )
                if term.early_discount_business_days
                else self.invoice_date + timedelta(days=term.discount_days)
            ),
            "amount": self.currency_id.round(base * term.discount_percentage / 100.0),
        }

    def _early_payment_can_apply(self):
        if self.move_type == "out_invoice":
            return self.early_payment_state == "available"
        return super()._early_payment_can_apply()

    def _early_payment_line_eligible(self, line):
        """Whether the discount takes off this line: the goods only when the
        payment terms say so, every product line otherwise."""
        return bool(
            line.display_type == "product"
            and line.product_id
            and (
                not self.invoice_payment_term_id.early_discount_goods_only
                or line.product_id.type == "consu"
            )
        )

    def _early_payment_eligible_lines(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(self._early_payment_line_eligible)

    def _early_payment_paid_on_time(self):
        """Whether the customer paid the discounted amount within the early
        payment date. Credit notes do not count as payments."""
        self.ensure_one()
        partials, _exchange = self._get_reconciled_invoices_partials()
        payments = [
            (amount, line)
            for _partial, amount, line in partials
            if line.move_id.move_type not in ("out_refund", "in_refund")
        ]
        if not payments:
            return False
        paid = sum(amount for amount, _line in payments)
        due = self.amount_total - self.early_payment_amount
        return (
            self.currency_id.compare_amounts(paid, due) >= 0
            and max(line.date for _amount, line in payments) <= self.early_payment_date
        )

    def _early_payment_adjust_credit_note(self, credit_note):
        super()._early_payment_adjust_credit_note(credit_note)
        if self.move_type != "out_invoice":
            return
        # Left in draft so the approvals of the company can gate it.
        percentage = self.invoice_payment_term_id.discount_percentage
        for line in credit_note.invoice_line_ids:
            if line.display_type != "product":
                continue
            if self._early_payment_line_eligible(line):
                line.price_unit = line.price_unit * percentage / 100.0
            else:
                line.unlink()

    def action_apply_early_payment(self):
        credit_note = super().action_apply_early_payment()
        if self.move_type != "out_invoice":
            return credit_note
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": credit_note.id,
            "view_mode": "form",
        }
