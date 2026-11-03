# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import frozendict


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("invoice_date_due")
    def _onchange_invoice_date_due_account_payment_term_partner_holiday(self):
        """Recompute the due date to the next available date according to
        the holiday periods set in the partner.

        It must only be re-calculated when a payment term is not set.
        This prevents the due date to be changed again and that another
        given number of days are added according to what is set on the
        payment term.
        """
        if (
            self.invoice_date_due
            and self.partner_id
            and not self.invoice_payment_term_id
        ):
            new_invoice_date_due = self.partner_id._get_valid_due_date(
                self.invoice_date_due
            )
            if new_invoice_date_due != self.invoice_date_due:
                self.invoice_date_due = new_invoice_date_due

    @api.depends("invoice_payment_term_id", "invoice_date", "invoice_date_due")
    def _compute_needed_terms(self):
        res = super()._compute_needed_terms()

        for move in self:
            if (
                move.is_invoice(include_receipts=True)
                and move.needed_terms
                and move.partner_id
            ):
                updated_terms = {}

                # Sort needed_terms by date_maturity
                # and save accumulated_delay_days
                # to compute date maturities correctly
                sorted_terms = sorted(
                    move.needed_terms.items(),
                    key=lambda t: t[0].get("date_maturity") or fields.Date.today(),
                )
                accumulated_delay_days = 0

                for key, values in sorted_terms:
                    current_maturity = key.get("date_maturity")
                    if current_maturity:
                        if accumulated_delay_days > 0:
                            current_maturity += timedelta(days=accumulated_delay_days)

                        new_maturity = move.partner_id._get_valid_due_date(
                            current_maturity
                        )

                        if new_maturity != current_maturity:
                            extra_delay = (new_maturity - current_maturity).days
                            accumulated_delay_days += extra_delay
                            current_maturity = new_maturity

                        new_key = frozendict(
                            {
                                **key,
                                "date_maturity": current_maturity,
                            }
                        )
                        updated_terms[new_key] = values
                        continue

                    updated_terms[key] = values
                move.needed_terms = updated_terms
        return res
