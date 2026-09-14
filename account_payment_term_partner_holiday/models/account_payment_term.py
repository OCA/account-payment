# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def _compute_terms(
        self,
        date_ref,
        currency,
        company,
        tax_amount,
        tax_amount_currency,
        sign,
        untaxed_amount,
        untaxed_amount_currency,
        cash_rounding=None,
    ):
        """Compute the due date taking into account the holiday periods
        set in the partner.

        Once an initial date resulting of the payment term is computed,
        compute the first available date after that.
        Then, apply_payment_days() and apply_holidays() to prevent
        incompatibilities.
        """
        result = super()._compute_terms(
            date_ref,
            currency,
            company,
            tax_amount,
            tax_amount_currency,
            sign,
            untaxed_amount,
            untaxed_amount_currency,
            cash_rounding,
        )
        ctx = self.env.context
        partner_id = ctx.get("move_partner_id", ctx.get("default_partner_id"))

        if not result or not partner_id:
            return result

        partner = self.env["res.partner"].browse(partner_id)

        is_dict_structure = isinstance(result, dict) and "line_ids" in result
        lines_to_iterate = result["line_ids"] if is_dict_structure else result

        for key, item in enumerate(lines_to_iterate):
            if isinstance(item, tuple) and len(item) == 3:
                vals = item[2]
            elif isinstance(item, dict):
                vals = item
            else:
                vals = getattr(item, "_values", {})

            if not vals or "date" not in vals:
                continue

            current_date = vals["date"]
            next_date = partner._get_valid_due_date(current_date)

            if next_date != current_date:
                line = self.line_ids.sorted(lambda x: x.value == "percent")[key]
                next_date = self.apply_payment_days(line, next_date)
                next_date = self.apply_holidays(next_date)
                vals["date"] = next_date

        return result
