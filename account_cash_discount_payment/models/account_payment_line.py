# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class PaymentLine(models.Model):

    _inherit = "account.payment.line"

    pay_with_discount = fields.Boolean(
        default=False,
    )
    pay_with_discount_allowed = fields.Boolean(
        compute="_compute_pay_with_discount_allowed",
    )
    toggle_pay_with_discount_allowed = fields.Boolean(
        compute="_compute_toggle_pay_with_discount_allowed",
    )
    discount_due_date = fields.Date(
        related="move_line_id.move_id.discount_due_date",
        readonly=True,
    )
    discount_amount = fields.Monetary(
        related="move_line_id.move_id.real_discount_amount",
        readonly=True,
    )

    def _compute_pay_with_discount_allowed(self):
        """
        Discount can be used only when the invoice has not already
        been paid partially or if the invoice has been reconciled only with
        refunds
        """
        for rec in self:
            allowed = False
            move_line = rec.move_line_id
            if move_line and move_line.move_id.has_discount:
                invoice = move_line.move_id
                allowed = invoice._can_pay_invoice_with_discount(check_due_date=False)
            rec.pay_with_discount_allowed = allowed

    def _compute_toggle_pay_with_discount_allowed(self):
        for rec in self:
            rec.toggle_pay_with_discount_allowed = (
                rec.pay_with_discount_allowed
                and rec.order_id.state not in ("uploaded", "cancelled")
            )

    @api.constrains(
        "pay_with_discount",
        "move_line_id",
    )
    def _check_pay_with_discount(self):
        for rec in self:
            if not rec.pay_with_discount:
                continue
            if not rec.pay_with_discount_allowed:
                raise ValidationError(
                    _(
                        "You can't pay with a discount if the payment line is "
                        "not linked to an invoice which has a discount."
                    )
                )

    @api.onchange(
        "discount_amount",
        "move_line_id",
        "pay_with_discount",
    )
    def _onchange_pay_with_discount(self):
        """
        This onchange should be executed completely only when the payment line
        is linked to a move line which is linked to an invoice which has a
        discount.

        If the above condition is ok, the amount will change based on the
        invoice total and invoice discount amount.
        """
        self._check_pay_with_discount()
        invoice = self.move_line_id.move_id
        currency = self.currency_id
        # When pay_with_discount is changed to False, we do not want to lose
        # the amount if the user changed it manually (related to the
        # _onchange_amount_with_discount which enable or disable the value
        # depending on the amount)
        change_base_amount = (
            float_compare(
                self.amount_currency,
                invoice.residual_with_discount,
                precision_rounding=currency.rounding,
            )
            == 0
        )
        if self.pay_with_discount:
            self.amount_currency = invoice.residual_with_discount
        elif change_base_amount:
            self.amount_currency = invoice.amount_residual

    @api.onchange(
        "amount_currency",
    )
    def _onchange_amount_with_discount(self):
        """
        This method will disable the pay_with_discount flag if the amount has
        been changed and if it doesn't equal to the invoice total amount with
        discount.
        """
        if not self.pay_with_discount_allowed or not self.pay_with_discount:
            return
        invoice = self.move_line_id.move_id
        currency = self.currency_id
        can_pay_with_discount = (
            float_compare(
                self.amount_currency,
                invoice.residual_with_discount,
                precision_rounding=currency.rounding,
            )
            == 0
        )
        if not can_pay_with_discount:
            self.pay_with_discount = False
            return {
                "warning": {
                    "title": _("Warning!"),
                    "message": _(
                        "You can't pay with a discount if "
                        "you don't pay all the invoice at once."
                    ),
                }
            }

    def _check_toggle_pay_with_discount_allowed(self):
        for rec in self:
            if not rec.toggle_pay_with_discount_allowed:
                raise UserError(
                    _(
                        "You can change the pay with discount value only if "
                        "there is a linked invoice with a discount and if the "
                        "payment order is not done. (Payment Order: %s)"
                    )
                    % (rec.order_id.name)
                )

    def toggle_pay_with_discount(self):
        self.ensure_one()
        self._check_toggle_pay_with_discount_allowed()
        self.pay_with_discount = not self.pay_with_discount
        self._onchange_pay_with_discount()
