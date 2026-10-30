# Copyright 2026 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_internal_transfer = fields.Boolean(
        string="Internal Transfer",
        tracking=True,
    )
    destination_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Destination Journal",
        domain="[('type', 'in', ('bank', 'cash')), "
        "('company_id', '=', company_id), "
        "('id', '!=', journal_id)]",
        check_company=True,
    )

    @api.depends("journal_id", "partner_id", "partner_type", "is_internal_transfer")
    def _compute_destination_account_id(self):
        internal_transfers = self.filtered("is_internal_transfer")
        regular_payments = self - internal_transfers
        if regular_payments:
            super(AccountPayment, regular_payments)._compute_destination_account_id()
        for payment in internal_transfers:
            payment.destination_account_id = (
                payment.journal_id.company_id.transfer_account_id
            )
        return

    @api.depends(
        "partner_id",
        "company_id",
        "payment_type",
        "destination_journal_id",
        "is_internal_transfer",
    )
    def _compute_available_partner_bank_ids(self):
        internal_transfers = self.filtered("is_internal_transfer")
        regular_payments = self - internal_transfers
        if regular_payments:
            super(
                AccountPayment, regular_payments
            )._compute_available_partner_bank_ids()
        for payment in internal_transfers:
            if payment.payment_type == "inbound":
                payment.available_partner_bank_ids = payment.journal_id.bank_account_id
            else:
                payment.available_partner_bank_ids = (
                    payment.destination_journal_id.bank_account_id
                )
        return

    def action_cancel(self):
        res = super().action_cancel()
        for payment in self:
            paired = payment.paired_internal_transfer_payment_id
            if paired and paired.state != "canceled":
                paired.action_cancel()
        return res

    def action_draft(self):
        res = super().action_draft()
        for payment in self:
            paired = payment.paired_internal_transfer_payment_id
            if paired and paired.state != "draft":
                paired.action_draft()
        return res

    def unlink(self):
        non_draft = self.filtered(
            lambda p: p.is_internal_transfer and p.state != "draft"
        )
        if non_draft:
            raise UserError(
                _(
                    "You can only delete internal transfers in draft state. "
                    "Please reset to draft first."
                )
            )
        paired = self.mapped("paired_internal_transfer_payment_id") - self
        res = super().unlink()
        if paired.exists():
            paired.unlink()
        return res

    def button_open_paired_payment(self):
        self.ensure_one()
        return {
            "name": _("Paired Payment"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "form",
            "res_id": self.paired_internal_transfer_payment_id.id,
        }

    def action_post(self):
        res = super().action_post()
        self.filtered(
            lambda p: p.is_internal_transfer
            and not p.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()
        return res

    def _create_paired_internal_transfer_payment(self):
        for payment in self:
            paired_payment = self.create(
                payment._prepare_paired_internal_transfer_values()
            )
            paired_payment.action_post()
            payment.paired_internal_transfer_payment_id = paired_payment
            body = _(
                "This payment has been created from: %(payment)s",
                payment=payment._get_html_link(),
            )
            paired_payment.message_post(body=body)
            body = _(
                "A paired payment has been created: %(payment)s",
                payment=paired_payment._get_html_link(),
            )
            payment.message_post(body=body)
            (payment + paired_payment)._reconcile_internal_transfer_lines()

    def _reconcile_internal_transfer_lines(self):
        payments_with_move = self.filtered("move_id")
        if len(payments_with_move) < 2:
            return
        transfer_account = payments_with_move[0].destination_account_id
        lines = payments_with_move.move_id.line_ids.filtered(
            lambda line: line.account_id == transfer_account and not line.reconciled
        )
        if lines:
            lines.reconcile()

    def _prepare_paired_internal_transfer_values(self):
        self.ensure_one()
        paired_payment_type = (
            "inbound" if self.payment_type == "outbound" else "outbound"
        )
        return {
            "journal_id": self.destination_journal_id.id,
            "amount": self.amount,
            "partner_id": self.company_id.partner_id.id,
            "currency_id": self.currency_id.id,
            "destination_journal_id": self.journal_id.id,
            "payment_type": paired_payment_type,
            "memo": self.memo or _("Internal Transfer"),
            "paired_internal_transfer_payment_id": self.id,
            "date": self.date,
            "is_internal_transfer": True,
        }

    def _prepare_move_line_default_vals(
        self, write_off_line_vals=None, force_balance=None
    ):
        line_vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance,
        )
        if self.is_internal_transfer and line_vals_list:
            if self.payment_type == "outbound":
                liquidity_line_name = _(
                    "Transfer to %s", self.destination_journal_id.name
                )
            else:
                liquidity_line_name = _(
                    "Transfer from %s", self.destination_journal_id.name
                )
            line_vals_list[0]["name"] = liquidity_line_name
            if len(line_vals_list) > 1:
                line_vals_list[1]["name"] = _("Internal Transfer")
        return line_vals_list
