# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, exceptions, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_token_id = fields.Many2one(
        "payment.token",
        check_company=True,
        domain="[('partner_id', 'child_of', commercial_partner_id), "
        "('company_id', '=', company_id)]",
    )
    has_payment_exception = fields.Boolean(copy=False)

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        # When an invoice with Payment token is posted, run the automatic payment
        to_pay = posted.filtered(lambda inv: inv.payment_token_id)
        to_pay.run_invoice_automatic_payments()
        return posted

    def run_invoice_automatic_payments(self):
        PaymentWizard = self.env["account.payment.register"]
        to_pay = self.filtered(lambda x: x.state == "posted" and not x.payment_ids)
        for inv in to_pay:
            if not inv.payment_token_id:
                raise exceptions.ValidationError(
                    _("Invoice %s is missing the Payment Token.", inv.display_name)
                )
            payment_vals = inv._prepare_payment_wizard_vals()
            payment_wizard = PaymentWizard.with_context(
                active_ids=inv.ids, active_model="account.move"
            ).create(payment_vals)
            try:
                payment_wizard._create_payments()
            except exceptions.ValidationError as e:
                inv.has_payment_exception = True
                inv.activity_schedule(
                    "mail.mail_activity_data_warning",
                    summary=_("Payment failed: %s") % e,
                )
                _logger.exception("Error on automatic payment for Invoice %s", inv.name)

    def _prepare_payment_wizard_vals(self):
        journal = self.payment_token_id.provider_id.journal_id
        method_line = journal.inbound_payment_method_line_ids[:1]
        return {
            "payment_token_id": self.payment_token_id.id,
            "journal_id": journal.id,
            "payment_method_line_id": method_line.id,
        }
