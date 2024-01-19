# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PaymentLine(models.Model):

    _inherit = "account.payment.line"

    discount_due_date = fields.Date(
        related="move_line_id.discount_date",
        readonly=True,
    )
    toggle_pay_with_discount_allowed = fields.Boolean(
        compute="_compute_toggle_pay_with_discount_allowed",
    )
    discount_amount = fields.Monetary(compute="_compute_discount_amount")
    pay_with_discount = fields.Boolean(
        default=False,
    )

    @api.depends(
        "move_line_id.amount_residual",
        "move_line_id.amount_residual_currency",
        "move_line_id.discount_percentage",
        "pay_with_discount",
    )
    def _compute_discount_amount(self):
        for rec in self:
            sign = -1 if rec.order_id.payment_type == "outbound" else 1
            if rec.currency_id:
                amount_without_disc = rec.move_line_id.amount_residual_currency
            else:
                amount_without_disc = rec.move_line_id.amount_residual
            rec.discount_amount = sign * (amount_without_disc) - rec.amount_currency

    @api.depends("order_id.state")
    def _compute_toggle_pay_with_discount_allowed(self):
        for rec in self:
            rec.toggle_pay_with_discount_allowed = rec.order_id.state not in (
                "uploaded",
                "cancel",
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
        """
        invoice_line = self.move_line_id

        if self.pay_with_discount:
            # apply discount
            self.amount_currency = invoice_line._get_amount_after_discount()[0]
        else:
            amount_currency = invoice_line.amount_residual_currency
            if self.order_id.payment_type == "outbound":
                amount_currency *= -1
            self.amount_currency = amount_currency

    @api.onchange(
        "amount_currency",
    )
    def _onchange_amount_with_discount(self):
        """
        This method will disable the pay_with_discount flag if the amount has
        been changed and if it doesn't equal to the amount with discount.
        """
        if not self.pay_with_discount:
            return
        invoice_line = self.move_line_id
        currency = self.currency_id
        amount_with_discount = invoice_line._get_amount_after_discount()[0]
        can_pay_with_discount = (
            float_compare(
                self.amount_currency,
                amount_with_discount,
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
