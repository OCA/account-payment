# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models
from odoo.exceptions import ValidationError

dict_payment_type = dict(
    inbound=["out_invoice", "in_refund", "out_receipt"],
    outbound=["in_invoice", "out_refund", "in_receipt"],
)


class AccountPaymentCounterLinesAbstract(models.AbstractModel):
    _name = "account.payment.counterpart.line.abstract"
    _inherit = "analytic.mixin"
    _description = "Counterpart line payment Abstract"

    company_id = fields.Many2one(
        comodel_name="res.company", compute="_compute_company_fields"
    )
    name = fields.Char(string="Description", required=True, default="/")
    account_id = fields.Many2one(
        "account.account",
        string="Account",
        required=True,
        ondelete="restrict",
        check_company=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_company_fields",
    )

    fully_paid = fields.Boolean(string="Fully Paid?")
    writeoff_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Write-off account",
        domain="[('deprecated', '=', False), ('company_ids', '=', company_id)]",
    )
    writeoff_amount = fields.Monetary(
        required=False,
        compute="_compute_amounts",
        currency_field="currency_id",
    )
    writeoff_amount_currency = fields.Monetary(
        required=False,
        compute="_compute_amounts",
        currency_field="currency_id",
    )

    @api.depends_context("company")
    @api.depends("company_id")
    def _compute_company_fields(self):
        company = self.env.company
        for rec in self:
            rec.company_id = company.id
            rec.currency_id = company.currency_id.id

    amount = fields.Monetary(required=True)
    amount_currency = fields.Monetary(
        string="Amount in Company Currency",
        compute="_compute_amounts",
        currency_field="currency_id",
    )
    aml_amount_residual = fields.Monetary(
        string="Amount Residual",
        compute="_compute_amounts",
        currency_field="currency_id",
    )
    residual_after_payment = fields.Monetary(
        compute="_compute_amounts",
        currency_field="currency_id",
    )
    aml_amount_residual_currency = fields.Monetary(
        string="Amount Residual Currency",
        compute="_compute_amounts",
        currency_field="currency_id",
    )
    residual_after_payment_currency = fields.Monetary(
        compute="_compute_amounts",
        currency_field="currency_id",
    )

    def _get_onchange_fields(self):
        return "aml_id.amount_residual", "amount", "fully_paid"

    @api.depends(lambda x: x._get_onchange_fields())
    def _compute_amounts(self):
        for rec in self:
            payment = rec.payment_id
            payment_date = (
                hasattr(payment, "payment_date")
                and payment.payment_date
                or payment.date
            )
            rec.amount_currency = payment.currency_id._convert(
                rec.amount,
                payment.company_id.currency_id,
                payment.company_id,
                date=payment_date,
            )
            rec.aml_amount_residual = rec.aml_id.amount_residual
            min_max = payment.payment_type == "outbound" and min or max
            rec.residual_after_payment = (
                not rec.fully_paid
                and min_max(rec.aml_id.amount_residual - rec.amount, 0)
                or 0.0
            )
            rec.writeoff_amount = (
                rec.fully_paid and (rec.aml_id.amount_residual - rec.amount) or 0.0
            )
            rec.aml_amount_residual_currency = rec.aml_id.amount_residual_currency
            rec.residual_after_payment_currency = (
                not rec.fully_paid
                and min_max(
                    rec.aml_id.amount_residual_currency - rec.amount_currency, 0
                )
                or 0.0
            )
            rec.writeoff_amount_currency = (
                rec.fully_paid
                and (rec.aml_id.amount_residual_currency - rec.amount_currency)
                or 0.0
            )

    partner_id = fields.Many2one("res.partner", string="Partner", ondelete="restrict")
    commercial_partner_id = fields.Many2one(related="partner_id.commercial_partner_id")
    move_id = fields.Many2one(
        "account.move", string="Journal Entry", ondelete="set null"
    )
    move_ids = fields.One2many(
        "account.move.line",
        "payment_line_id",
        string="Journal Entries Created",
    )
    aml_id = fields.Many2one(
        "account.move.line", string="Journal Item to Reconcile", ondelete="set null"
    )
    aml_date_maturity = fields.Date(
        string="Date Maturity", required=False, related="aml_id.date_maturity"
    )

    @api.onchange("move_id", "aml_id")
    def _onchange_move_id(self):
        aml_model = self.env["account.move.line"]
        for rec in self:
            dict_payment_type.get(rec.payment_id.payment_type, [])
            if rec.move_id and not rec.aml_id:
                domain = [
                    ("move_id", "=", rec.move_id.id),
                    ("amount_residual", "!=", 0.0),
                ]
                lines_ordered = aml_model.search(
                    domain, order="date_maturity ASC", limit=1
                )
                if lines_ordered:
                    rec.aml_id = lines_ordered.id
            if rec.aml_id:
                rec.move_id = rec.aml_id.move_id.id
                rec.account_id = rec.aml_id.account_id.id
                rec.amount = rec.aml_id.amount_residual
                rec.partner_id = rec.aml_id.partner_id.id
                if rec.move_id.move_type == "entry":
                    if rec.payment_id.payment_type == "outbound":
                        rec.amount = -rec.aml_id.amount_residual
                    else:
                        rec.amount = rec.aml_id.amount_residual

    @api.constrains("amount")
    def constrains_amount_residual(self):
        for rec in self:
            if (
                rec.aml_id
                and 0 < rec.aml_amount_residual_currency < rec.amount_currency
            ):
                move_name = rec.aml_id.move_id.name or rec.aml_id.name
                raise ValidationError(
                    self.env._(
                        "the amount exceeds the residual amount, "
                        "please check the invoice %s",
                        move_name,
                    )
                )
