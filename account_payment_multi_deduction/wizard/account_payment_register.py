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

    def _update_vals_deduction(self, moves):
        move_lines = moves.mapped("line_ids")
        analytic = {}
        [
            analytic.update(item)
            for item in move_lines.mapped("analytic_distribution")
            if item
        ]
        self.analytic_distribution = analytic

    def _update_vals_multi_deduction(self, moves):
        move_lines = moves.mapped("line_ids")
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
        moves = self.env["account.move"].browse(active_ids)
        if self.payment_difference_handling == "reconcile":
            self._update_vals_deduction(moves)
        if self.payment_difference_handling == "reconcile_multi_deduct":
            self._update_vals_multi_deduction(moves)

    @api.constrains("deduction_ids", "payment_difference_handling")
    def _check_deduction_amount(self):
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
        for rec in self:
            rec.deduct_residual = rec.payment_difference - sum(
                rec.deduction_ids.mapped("amount")
            )

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        # payment difference
        if (
            not self.currency_id.is_zero(self.payment_difference)
            and self.payment_difference_handling == "reconcile"
        ):
            payment_vals["write_off_line_vals"][0][
                "analytic_distribution"
            ] = self.analytic_distribution
        # multi deduction
        elif (
            self.payment_difference
            and self.payment_difference_handling == "reconcile_multi_deduct"
        ):
            payment_vals["write_off_line_vals"] = [
                self._prepare_deduct_move_line(deduct)
                for deduct in self.deduction_ids.filtered(lambda l: not l.is_open)
            ]
            payment_vals["is_multi_deduction"] = True
        return payment_vals

    def _prepare_deduct_move_line(self, deduct):
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
