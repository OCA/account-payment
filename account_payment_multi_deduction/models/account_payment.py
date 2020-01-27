# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_difference_handling = fields.Selection(
        selection_add=[
            ("reconcile_multi_deduct", "Mark invoice as fully paid (multi deduct)")
        ]
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

    @api.constrains("deduction_ids")
    def _check_deduction_amount(self):
        self.ensure_one()
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        if self.payment_difference_handling == "reconcile_multi_deduct":
            if (
                float_compare(
                    self.payment_difference,
                    sum(self.deduction_ids.mapped("amount")),
                    precision_digits=prec_digits,
                )
                != 0
            ):
                raise UserError(
                    _("The total deduction should be %s") % self.payment_difference
                )

    @api.depends("payment_difference", "deduction_ids")
    def _compute_deduct_residual(self):
        for rec in self:
            rec.deduct_residual = rec.payment_difference - sum(
                rec.deduction_ids.mapped("amount")
            )

    def _prepare_payment_moves(self):
        """ If payment handling is reconcile_multi_deduct, modify line_ids
            using multi deduction table """

        x_payments = self.filtered(
            lambda l: l.payment_type != "transfer"
            and l.payment_difference_handling == "reconcile_multi_deduct"
        )

        # Normal payments, prepare move vals as normal
        all_move_vals = super(
            AccountPayment, self - x_payments
        )._prepare_payment_moves()

        # = Start multi deduciton case =
        x_payments.write({"payment_difference_handling": "reconcile"})
        for payment in x_payments:

            def no_writeoff_line(line):
                if not (
                    line[2]["name"] == payment.writeoff_label
                    and line[2]["payment_id"] == payment.id
                ):
                    return line

            move_vals = super(AccountPayment, payment)._prepare_payment_moves()
            # Remove normal writeoff line
            move_vals[0]["line_ids"] = list(
                filter(no_writeoff_line, move_vals[0]["line_ids"])
            )
            # Prepare required variables
            company_currency = payment.company_id.currency_id
            write_off_amount = -payment.payment_difference or 0.0
            write_off_balance = 0.0
            currency_id = False
            if payment.currency_id == company_currency:
                write_off_balance = write_off_amount
            else:  # Multi-currencies.
                write_off_balance = payment.currency_id._convert(
                    write_off_amount,
                    company_currency,
                    payment.company_id,
                    payment.payment_date,
                )
                currency_id = payment.currency_id.id
            # Create new line_ids with multi deduction table
            if write_off_balance:
                for deduct in payment.deduction_ids:
                    wo_amount_currency = deduct.amount
                    wo_amount = payment.currency_id._convert(
                        wo_amount_currency,
                        company_currency,
                        payment.company_id,
                        payment.payment_date,
                    )
                    move_vals[0]["line_ids"].append(
                        (
                            0,
                            0,
                            {
                                "name": deduct.name,
                                "amount_currency": wo_amount_currency,
                                "currency_id": currency_id,
                                "debit": wo_amount > 0.0 and wo_amount or 0.0,
                                "credit": wo_amount < 0.0 and -wo_amount or 0.0,
                                "date_maturity": payment.payment_date,
                                "partner_id": payment.partner_id.id,
                                "account_id": deduct.account_id.id,
                                "payment_id": payment.id,
                            },
                        )
                    )

            all_move_vals += move_vals
        # Set diff handling back to original
        x_payments.write({"payment_difference_handling": "reconcile_multi_deduct"})
        return all_move_vals


class AccountPaymentDeduction(models.Model):
    _name = "account.payment.deduction"
    _description = "Payment Deduction"

    payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
        readonly=True,
        ondelete="cascade",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="payment_id.currency_id",
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        domain=[("deprecated", "=", False)],
        required=True,
    )
    amount = fields.Monetary(string="Deduction Amount", required=True)
    name = fields.Char(string="Label", required=True)
