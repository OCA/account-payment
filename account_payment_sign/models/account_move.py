# Copyright 2024 Alexandre D. Díaz - Grupo Isonor

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_default_require_signature(self):
        return self.env.company.invoice_portal_confirmation_sign

    require_signature = fields.Boolean(
        "Online Signature",
        default=_get_default_require_signature,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Request a online signature to the customer.",
    )
    signature = fields.Image(
        help="Signature received through the portal.",
        copy=False,
        attachment=True,
        max_width=1024,
        max_height=1024,
    )
    signed_by = fields.Char(help="Name of the person that signed the INV.", copy=False)
    signed_on = fields.Datetime(help="Date of the signature.", copy=False)

    def has_to_be_signed(self, include_draft=False):
        return (
            (self.state == "posted" or (self.state == "draft" and include_draft))
            and self.move_type == "out_invoice"
            and self.require_signature
            and not self.signature
        )

    def has_to_be_paid(self, include_draft=False):
        tx_ids = self.transaction_ids.filtered(
            lambda tx: tx.state in ("pending", "authorized", "done")
        )
        pending_manual_txs = tx_ids.filtered(
            lambda tx: tx.state == "pending" and tx.provider in ("none", "transfer")
        )
        return (
            (self.state == "posted" or (self.state == "draft" and include_draft))
            and self.payment_state in ("not_paid", "partial")
            and self.amount_total
            and self.move_type == "out_invoice"
            and (
                pending_manual_txs
                or not tx_ids
                or self.amount_paid
                and self.amount_total
            )
        )
