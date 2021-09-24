# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

READONLY_STATES = {
    "draft": [("readonly", False)],
}
DISCOUNT_ALLOWED_TYPES = (
    "in_invoice",
    "in_refund",
    "out_invoice",
)


class AccountMove(models.Model):

    _inherit = "account.move"

    is_cash_discount_allowed = fields.Boolean(
        compute="_compute_is_cash_discount_allowed",
    )
    discount_percent = fields.Float(
        string="Discount (%)",
        readonly=True,
        states=READONLY_STATES,
        digits="Discount",
    )
    amount_total_with_discount = fields.Monetary(
        string="Total (with discount)",
        compute="_compute_amount_total_with_discount",
        store=True,
    )
    residual_with_discount = fields.Monetary(compute="_compute_residual_with_discount")
    discount_amount = fields.Monetary(
        compute="_compute_discount_amount",
        store=True,
    )
    real_discount_amount = fields.Monetary(
        compute="_compute_real_discount_amount",
        string="Discount amount (minus related refunds amount)",
    )
    refunds_discount_amount = fields.Monetary(
        compute="_compute_refunds_discount_amount",
        store=True,
    )
    discount_delay = fields.Integer(
        string="Discount Delay (days)", readonly=True, states=READONLY_STATES
    )
    discount_due_date = fields.Date(readonly=True, states=READONLY_STATES)
    discount_due_date_readonly = fields.Date(
        compute="_compute_discount_due_date",
    )
    has_discount = fields.Boolean(
        compute="_compute_has_discount",
        store=True,
    )
    discount_base_date = fields.Date(
        compute="_compute_discount_base_date",
    )

    @api.depends("move_type")
    def _compute_is_cash_discount_allowed(self):
        for rec in self:
            rec.is_cash_discount_allowed = rec.move_type in DISCOUNT_ALLOWED_TYPES

    @api.depends(
        "amount_total",
        "amount_untaxed",
        "discount_percent",
        "company_id",
    )
    def _compute_discount_amount(self):
        for rec in self:
            discount_amount = 0.0
            if rec.discount_percent != 0.0:
                base_amount_type = rec.company_id.cash_discount_base_amount_type
                base_amount = (
                    base_amount_type == "untaxed"
                    and rec.amount_untaxed
                    or rec.amount_total
                )
                discount_amount = base_amount * (rec.discount_percent / 100)
            rec.discount_amount = discount_amount

    @api.depends(
        "amount_total",
        "refunds_discount_amount",
        "amount_residual",
    )
    def _compute_residual_with_discount(self):
        for rec in self:
            rec.residual_with_discount = (
                rec.amount_residual - rec.discount_amount + rec.refunds_discount_amount
            )

    @api.depends(
        "amount_total",
        "line_ids.matched_credit_ids.credit_move_id.move_id.move_type",
        "line_ids.matched_credit_ids.credit_move_id.move_id.discount_amount",
        "line_ids.matched_debit_ids.debit_move_id.move_id.move_type",
        "line_ids.matched_credit_ids.debit_move_id.move_id.discount_amount",
    )
    def _compute_refunds_discount_amount(self):
        for rec in self:
            rec.refunds_discount_amount = rec._get_refunds_amount_total()["discount"]

    @api.depends(
        "discount_amount",
        "refunds_discount_amount",
    )
    def _compute_real_discount_amount(self):
        for rec in self:
            rec.real_discount_amount = rec.discount_amount - rec.refunds_discount_amount

    @api.depends(
        "amount_total",
        "discount_amount",
    )
    def _compute_amount_total_with_discount(self):
        for rec in self:
            rec.amount_total_with_discount = rec.amount_total - rec.discount_amount

    @api.depends(
        "discount_due_date",
    )
    def _compute_discount_due_date(self):
        for rec in self:
            rec.discount_due_date_readonly = rec.discount_due_date

    @api.depends(
        "discount_amount",
        "discount_due_date",
    )
    def _compute_has_discount(self):
        for rec in self:
            rec.has_discount = (
                rec.discount_amount != 0
                and rec.discount_due_date != 0
                and rec.move_type in DISCOUNT_ALLOWED_TYPES
            )

    @api.depends("invoice_date")
    def _compute_discount_base_date(self):
        for rec in self:
            if rec.invoice_date:
                rec.discount_base_date = rec.invoice_date
            else:
                rec.discount_base_date = fields.Date.context_today(rec)

    @api.onchange(
        "has_discount",
        "discount_base_date",
        "discount_amount",
        "discount_delay",
    )
    def _onchange_discount_delay(self):
        for rec in self:
            skip = (
                rec.discount_amount == 0
                or rec.discount_delay == 0
                or rec.move_type not in DISCOUNT_ALLOWED_TYPES
            )
            if skip:
                continue
            discount_base_date = fields.Date.from_string(rec.discount_base_date)
            due_date = discount_base_date + timedelta(days=rec.discount_delay)
            rec.discount_due_date = due_date

    @api.onchange(
        "partner_id",
        "company_id",
    )
    def _onchange_partner_id(self):
        old_payment_term_id = self.invoice_payment_term_id
        res = super(AccountMove, self)._onchange_partner_id()
        if self.invoice_payment_term_id != old_payment_term_id:
            # be sure to load discount options based on the payment term.
            # It was not loaded when creating a vendor bill from a purchase
            # order.
            self._onchange_payment_term_discount_options()
        return res

    @api.onchange(
        "invoice_payment_term_id",
    )
    def _onchange_payment_term_discount_options(self):
        payment_term = self.invoice_payment_term_id
        if payment_term and self.move_type in DISCOUNT_ALLOWED_TYPES:
            self.discount_percent = payment_term.discount_percent
            self.discount_delay = payment_term.discount_delay

    def _get_payment_move_lines(self):
        self.ensure_one()
        line_ids = []
        for line in self.line_ids:
            account_type = line.account_id.user_type_id.type
            if account_type not in ("receivable", "payable"):
                continue
            line_ids.extend([rp.credit_move_id.id for rp in line.matched_credit_ids])
            line_ids.extend([rp.debit_move_id.id for rp in line.matched_debit_ids])
        return self.env["account.move.line"].browse(set(line_ids))

    def _get_refunds_amount_total(self):
        self.ensure_one()
        refunds_discount_total = 0.0
        refunds_amount_total = 0.0
        inv_type = self.move_type
        expected_refund_type = False
        if inv_type in DISCOUNT_ALLOWED_TYPES and inv_type.endswith("invoice"):
            expected_refund_type = inv_type.replace("invoice", "refund")
        for pmove_line in self._get_payment_move_lines():
            pmove_line_move = pmove_line.move_id
            if pmove_line_move and pmove_line_move.move_type == expected_refund_type:
                refunds_discount_total += pmove_line_move.discount_amount
                refunds_amount_total += pmove_line_move.amount_total
        return {"discount": refunds_discount_total, "total": refunds_amount_total}

    def action_post(self):
        for move in self:
            if move.move_type not in DISCOUNT_ALLOWED_TYPES:
                continue
            move._onchange_discount_delay()
            if not move.discount_due_date and move.discount_amount != 0.0:
                raise UserError(
                    _(
                        "You can't set a discount amount if there is no "
                        "discount due date. (Move ID: %s)"
                    )
                    % (move.id,)
                )
        return super(AccountMove, self).action_post()

    def _reverse_move_vals(self, default_values, cancel=True):
        res = super(AccountMove, self)._reverse_move_vals(default_values, cancel=cancel)
        partner_id = self.partner_id
        if self.move_type in DISCOUNT_ALLOWED_TYPES and partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            payment_term = partner.property_supplier_payment_term_id
            res["invoice_payment_term_id"] = payment_term.id
        return res
