# Copyright 2019-2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    force_early_discount = fields.Boolean(
        string="Apply Early Payment Discount Past Date",
        help="Force early payment discount even if the date is past and the flag is"
        " not set on the invoices.\n"
        "Note that early payment discounts will be applied for invoices having"
        "the flag set, even if this checkbox is not marked.",
    )
    show_force_early_discount = fields.Boolean(
        compute="_compute_show_force_early_discount"
    )
    with_forced_early_discount = fields.Boolean(
        compute="_compute_with_forced_early_discount"
    )

    @api.depends("force_early_discount", "line_ids", "payment_date")
    def _compute_with_forced_early_discount(self):
        """Check if an early payment discount is forced on the wizard

        An early payment discount is forced if:
        - Early payment discount is available on any invoice and invoice is marked
          with force early discount.
        - Early payment discount is available on any invoice and wizard is marked
          with force early discount."""
        for wizard in self:
            if wizard.force_early_discount:
                wizard.with_forced_early_discount = True
                continue
            lines_with_forced_discount_past_date = wizard.line_ids.filtered(
                lambda l: l.discount_amount_currency
                and l.discount_date < wizard.payment_date
                and l.move_id.force_early_discount
            )
            wizard.with_forced_early_discount = bool(
                lines_with_forced_discount_past_date
            )

    @api.depends("line_ids")
    def _compute_show_force_early_discount(self):
        for wizard in self:
            # If at least one invoice has late discounts on its move lines
            wizard.show_force_early_discount = wizard.line_ids.filtered(
                lambda l: l.discount_amount_currency
                and l.discount_date < wizard.payment_date
            )
            # If any invoice has force_early_discount
            any_invoice_with_forced_discount = any(
                wizard.line_ids.mapped("move_id.force_early_discount")
            )

    @api.depends("with_forced_early_discount", "force_early_discount")
    def _compute_from_lines(self):
        return super()._compute_from_lines()

    @api.depends(
        "with_forced_early_discount",
    )
    def _compute_amount(self):
        return super()._compute_amount()

    def _apply_force_early_payment_discount_ctx(self, batch_result):
        if self.force_early_discount:
            batch_result["lines"] = batch_result["lines"].with_context(
                _force_early_discount=batch_result["lines"].move_id.ids
            )
        else:
            force_discount_lines = batch_result["lines"].filtered(
                lambda li: li.move_id.force_early_discount
            )
            if force_discount_lines:
                batch_result["lines"] = batch_result["lines"].with_context(
                    _force_early_discount=force_discount_lines.move_id.ids
                )
        return batch_result

    def _create_payment_vals_from_wizard(self, batch_result):
        # Set ctx to be used on account.move._is_eligible_for_early_payment_discount
        batch_result = self._apply_force_early_payment_discount_ctx(batch_result)
        return super()._create_payment_vals_from_wizard(batch_result)

    def _create_payment_vals_from_batch(self, batch_result):
        # Set ctx to be used on account.move._is_eligible_for_early_payment_discount
        batch_result = self._apply_force_early_payment_discount_ctx(batch_result)
        return super()._create_payment_vals_from_batch(batch_result)

    def _get_total_amounts_to_pay(self, batch_results):
        # Set ctx to be used on account.move._is_eligible_for_early_payment_discount
        if self.with_forced_early_discount:
            force_ids = []
            for batch_result in batch_results:
                if self.force_early_discount:
                    batch_result["lines"] = batch_result["lines"].with_context(
                        _force_early_discount=batch_result["lines"].move_id.ids
                    )
                    force_ids += batch_result["lines"].move_id.ids
                else:
                    force_discount_lines = batch_result["lines"].filtered(
                        lambda li: li.move_id.force_early_discount
                    )
                    if force_discount_lines:
                        batch_result["lines"] = batch_result["lines"].with_context(
                            _force_early_discount=force_discount_lines.move_id.ids
                        )
                        force_ids += force_discount_lines.move_id.ids
                if force_ids:
                    self = self.with_context(_force_early_discount=force_ids)
        return super()._get_total_amounts_to_pay(batch_results)
