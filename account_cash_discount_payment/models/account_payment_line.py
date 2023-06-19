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

            if self.currency_id:
                amount_without_disc = rec.move_line_id.amount_residual_currency
            else:
                amount_without_disc = rec.move_line_id.amount_residual
            rec.discount_amount = sign * (
                amount_without_disc * rec.move_line_id.discount_percentage / 100
            )

    @api.depends("order_id.state")
    def _compute_toggle_pay_with_discount_allowed(self):
        for rec in self:
            rec.toggle_pay_with_discount_allowed = rec.order_id.state not in (
                "uploaded",
                "cancelled",
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
        currency = self.currency_id

        # compute discount amount
        if self.currency_id:
            base_amount = invoice_line.amount_residual_currency
        else:
            base_amount = invoice_line.amount_residual

        if self.order_id.payment_type == "outbound":
            amount_with_discount = base_amount * -1
        # apply discount
        amount_with_discount *= 1 - (invoice_line.discount_percentage / 100)

        # When pay_with_discount is changed to False, we do not want to lose
        # the amount if the user changed it manually (related to the
        # _onchange_amount_with_discount which enable or disable the value
        # depending on the amount)
        change_base_amount = (
            float_compare(
                self.amount_currency,
                amount_with_discount,
                precision_rounding=currency.rounding,
            )
            == 0
        )
        if self.pay_with_discount:
            # apply discount
            self.amount_currency = amount_with_discount
            # update discount_amount_currency on aml
            # amount_with_discount is negative
            self.move_line_id.discount_amount_currency = (
                invoice_line.amount_currency - (base_amount + amount_with_discount)
            )
            self.move_line_id.discount_balance = invoice_line.balance - (
                base_amount + amount_with_discount
            )
        elif change_base_amount:
            if self.currency_id:
                amount_currency = invoice_line.amount_residual_currency
            else:
                amount_currency = invoice_line.amount_residual

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
        can_pay_with_discount = (
            float_compare(
                self.amount_currency,
                invoice_line.amount_residual * -1,
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
