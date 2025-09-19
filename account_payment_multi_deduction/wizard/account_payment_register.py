# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountPaymentRegister(models.TransientModel):
    _name = "account.payment.register"
    _inherit = ["account.payment.register", "analytic.mixin"]

    payment_difference_handling = fields.Selection(
        selection_add=[
            ("reconcile_multi_deduct", "Mark invoice as fully paid (multi deduct)")
        ],
        ondelete={"reconcile_multi_deduct": "cascade"},
    )
    deduct_residual = fields.Monetary(
        string="Remainings", compute="_compute_deduct_residual"
    )
    deduction_ids = fields.One2many(
        comodel_name="account.payment.deduction",
        inverse_name="payment_id",
        string="Deductions",
        copy=False,
        help="Sum of deduction amount(s) must equal to the payment difference",
    )
    deduct_analytic_distribution = fields.Json()

    def _update_vals_deduction(self, move_lines):
        analytic = {}
        [
            analytic.update(item)
            for item in move_lines.mapped("analytic_distribution")
            if item
        ]
        self.analytic_distribution = analytic

    def _update_vals_multi_deduction(self, move_lines):
        analytic = {}
        [
            analytic.update(item)
            for item in move_lines.mapped("analytic_distribution")
            if item
        ]
        self.deduct_analytic_distribution = analytic

    @api.onchange("payment_difference", "payment_difference_handling")
    def _onchange_default_deduction(self):
        active_ids = self.env.context.get("active_ids", [])
        moves = self.env["account.move.line"].browse(active_ids)
        if self.payment_difference_handling == "reconcile":
            self._update_vals_deduction(moves)
        if self.payment_difference_handling == "reconcile_multi_deduct":
            self._update_vals_multi_deduction(moves)

    @api.constrains("deduction_ids", "payment_difference_handling")
    def _check_deduction_amount(self):
        """
        Validates that the sum of the deduction amounts (deduction_ids)
        is equal to the payment difference (payment_difference) when using
        the multi deduction mode. If not, raises an error to prevent
        accounting inconsistencies in the payment registration.
        """
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        for rec in self:
            if rec.payment_difference_handling == "reconcile_multi_deduct":
                if (
                    float_compare(
                        rec.payment_difference,
                        sum(rec.deduction_ids.mapped("amount")),
                        precision_digits=prec_digits,
                    )
                    != 0
                ):
                    raise UserError(
                        _("The total deduction should be %s") % rec.payment_difference
                    )

    @api.depends("payment_difference", "deduction_ids")
    def _compute_deduct_residual(self):
        """
        Computes the remaining amount to be deducted (deduct_residual)
        by subtracting the sum of all deduction amounts from the payment difference.
        This is used to track how much is left to allocate in multi deduction mode.
        """
        for rec in self:
            rec.deduct_residual = rec.payment_difference - sum(
                rec.deduction_ids.mapped("amount")
            )

    def _create_payment_vals_from_wizard(self, batch_result):
        """
        Generates the payment values dictionary to be used for payment creation.
        Adds analytic distribution to the write-off line if handling a single
        payment difference. If handling multi deduction, replaces the write-off
        lines with the prepared deduction lines and marks the payment as multi
        deduction. Returns the final payment values dict.
        """
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        # payment difference
        if self.payment_difference_handling == "reconcile":
            if not self.currency_id.is_zero(self.payment_difference):
                payment_vals["write_off_line_vals"][0][
                    "analytic_distribution"
                ] = self.analytic_distribution
        # multi deduction
        elif self.payment_difference_handling == "reconcile_multi_deduct":
            if self.payment_difference:
                payment_vals["write_off_line_vals"] = [
                    self._prepare_deduct_move_line(deduct)
                    for deduct in self.deduction_ids.filtered(
                        lambda deduction: not deduction.is_open
                    )
                ]
                payment_vals["is_multi_deduction"] = True
        return payment_vals

    def _prepare_deduct_move_line(self, deduct):
        """
        Prepares the dictionary for a single deduction line to be used as a
        write-off line in multi deduction payments.
        Calculates the amount, balance, and analytic distribution for the deduction.
        """
        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            self.currency_id,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )
        write_off_amount_currency = (
            deduct.amount if self.payment_type == "inbound" else -deduct.amount
        )
        write_off_balance = self.company_id.currency_id.round(
            write_off_amount_currency * conversion_rate
        )
        return {
            "name": deduct.name,
            "account_id": deduct.account_id.id,
            "partner_id": self.partner_id.id,
            "currency_id": self.currency_id.id,
            "amount_currency": write_off_amount_currency,
            "balance": write_off_balance,
            "analytic_distribution": deduct.analytic_distribution,
        }
