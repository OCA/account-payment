# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    early_payment_date = fields.Date(
        compute="_compute_early_payment",
        store=True,
        help="Last day to pay to earn the early payment discount.",
    )
    early_payment_amount = fields.Monetary(
        compute="_compute_early_payment",
        store=True,
        help="What the early payment discount takes off this invoice.",
    )
    early_payment_can_apply = fields.Boolean(
        compute="_compute_early_payment_can_apply",
        help="The discount is earned and its credit note is not issued yet.",
    )
    early_payment_credit_note_id = fields.Many2one(
        "account.move",
        readonly=True,
        copy=False,
        help="Credit note that settles the early payment discount of this invoice.",
    )
    is_early_payment_refund = fields.Boolean(
        readonly=True,
        copy=False,
        help="This credit note settles an early payment discount.",
    )

    @api.depends("move_type", "invoice_date", "company_id")
    def _compute_early_payment(self):
        """Extending modules add their dependencies and compute the values in
        `_get_early_payment_values` for the move types they handle."""
        for move in self:
            values = move._get_early_payment_values()
            move.early_payment_date = values.get("date", False)
            move.early_payment_amount = values.get("amount", 0.0)

    @api.depends("early_payment_amount", "early_payment_credit_note_id.state", "state")
    def _compute_early_payment_can_apply(self):
        for move in self:
            move.early_payment_can_apply = move._early_payment_can_apply()

    def _get_early_payment_values(self):
        """Date and amount of the discount of this move, empty when none."""
        self.ensure_one()
        return {}

    def _early_payment_can_apply(self):
        """Whether the discount is earned and still to settle."""
        self.ensure_one()
        credit_note = self.early_payment_credit_note_id
        return bool(
            self.state == "posted"
            and self.early_payment_amount > 0
            and (not credit_note or credit_note.state == "cancel")
        )

    def _early_payment_credit_note_values(self):
        """Defaults of the credit note that settles the discount."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        return {
            "invoice_date": today,
            "date": today,
            "ref": self.env._("Early payment discount of %s", self.name),
            "invoice_payment_term_id": False,
            "is_early_payment_refund": True,
        }

    def _early_payment_adjust_credit_note(self, credit_note):
        """Turn the full reversal into the discount: extending modules scale
        or drop its lines and post it when their flow says so."""
        self.ensure_one()

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted.filtered("is_early_payment_refund"):
            invoice = move.reversed_entry_id
            (invoice.line_ids + move.line_ids).filtered(
                lambda line: line.account_type
                in ("asset_receivable", "liability_payable")
                and not line.reconciled
            ).reconcile()
        return posted

    def action_apply_early_payment(self):
        """Settle the early payment discount with a credit note.

        :return: the credit note, adjusted (and posted) by the extending module.
        """
        self.ensure_one()
        if not self.early_payment_can_apply:
            raise UserError(
                self.env._(
                    "The early payment discount of %s cannot be applied.", self.name
                )
            )
        credit_note = self._reverse_moves([self._early_payment_credit_note_values()])
        self._early_payment_adjust_credit_note(credit_note)
        self.early_payment_credit_note_id = credit_note
        return credit_note
