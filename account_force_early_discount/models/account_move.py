# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    display_force_early_discount = fields.Boolean(
        compute="_compute_display_force_early_discount"
    )
    force_early_discount = fields.Boolean(
        "Force early payment discount",
        default=False,
        help="If marked, early payment discount will be applied even if the "
        "discount date is passed",
    )

    def _get_display_force_early_discount(self):
        self.ensure_one()
        if self.state == "draft":
            if (
                self.invoice_payment_term_id.discount_days
                and self.invoice_payment_term_id.discount_percentage
            ):
                return True
        elif self.state == "posted":
            first_payment_term_line = self._get_first_payment_term_line()
            if (
                first_payment_term_line.discount_date
                and first_payment_term_line.discount_amount
            ):
                return True
        return False

    @api.depends(
        "invoice_payment_term_id",
        "invoice_payment_term_id.early_discount",
        "force_early_discount",
        "state",
    )
    def _compute_display_force_early_discount(self):
        """Compute discount financial discount fields"""
        for rec in self:
            rec.display_force_early_discount = rec._get_display_force_early_discount()

    def _get_first_payment_term_line(self):
        self.ensure_one()
        payment_term_lines = self.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        return fields.first(payment_term_lines.sorted("date_maturity"))

    def _is_eligible_for_early_payment_discount(self, currency, reference_date):
        force_move_ids = self.env.context.get("_force_early_discount")
        if self.force_early_discount or force_move_ids:
            payment_terms = self.line_ids.filtered(
                lambda line: line.display_type == "payment_term"
            )
            return (
                (self.force_early_discount or self.id in force_move_ids)
                and self.currency_id == currency
                and self.move_type
                in ("out_invoice", "out_receipt", "in_invoice", "in_receipt")
                and self.invoice_payment_term_id.early_discount
                and not (
                    payment_terms.sudo().matched_debit_ids
                    + payment_terms.sudo().matched_credit_ids
                )
            )
        return super()._is_eligible_for_early_payment_discount(currency, reference_date)
