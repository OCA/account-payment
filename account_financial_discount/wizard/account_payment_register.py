# Copyright 2019-2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.tools import float_compare


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    force_financial_discount = fields.Boolean(
        string="Apply Financial Discount Past Date",
        help="Force financial discount even if the date is past and the flag is"
        " not set on the invoices.\n"
        "Note that financial discounts will be applied for invoices having"
        "the flag set, even if this checkbox is not marked.",
    )
    show_force_financial_discount = fields.Boolean(
        compute="_compute_show_force_financial_discount"
    )
    with_financial_discount = fields.Boolean(compute="_compute_with_financial_discount")
    payment_method_id = fields.Many2one(compute="_compute_payment_method_id")

    @api.depends(
        "payment_type",
        "journal_id.inbound_payment_method_ids",
        "journal_id.outbound_payment_method_ids",
    )
    def _compute_payment_method_id(self):
        # method to compute payment_method_id with same way as in origin method
        # but do not erase it after as complex chain of dependency introduced
        # here causes erasing selected payment)method_id on change of payment_date
        for wizard in self:
            if not wizard.payment_method_id:
                if wizard.payment_type == "inbound":
                    available_payment_methods = (
                        wizard.journal_id.inbound_payment_method_ids
                    )
                else:
                    available_payment_methods = (
                        wizard.journal_id.outbound_payment_method_ids
                    )

                # Select the first available one by default.
                if available_payment_methods:
                    wizard.payment_method_id = available_payment_methods[0]._origin
                else:
                    wizard.payment_method_id = False

    @api.depends("force_financial_discount", "line_ids", "payment_date")
    def _compute_with_financial_discount(self):
        """Check if a financial discount is applied on the wizard

        A financial discount is applied if:
        - Financial discount is available on any invoice and its Date is before
          actual payment date.
        - Financial discount is available on any invoice and invoice is marked
          with force financial discount.
        - Financial discount is available on any invoice and wizard is marked
          with force financial discount."""
        for wizard in self:
            if wizard.force_financial_discount:
                wizard.with_financial_discount = True
                continue
            lines_with_discount = wizard.line_ids.filtered(lambda l: l.amount_discount)
            lines_with_discount_before_payment_date = lines_with_discount.filtered(
                lambda l: l.date_discount <= wizard.payment_date
            )
            lines_with_forced_discount = lines_with_discount.mapped(
                "move_id.force_financial_discount"
            )
            wizard.with_financial_discount = bool(
                lines_with_discount_before_payment_date or lines_with_forced_discount
            )

    @api.depends("line_ids")
    def _compute_show_force_financial_discount(self):
        for wizard in self:
            # If at least one invoice has discounts on its move lines
            any_invoice_with_discount = wizard.line_ids.filtered(
                lambda l: l.amount_discount
            )
            # If not all invoices have discounts available
            not_all_invoices_with_discounts_available = not all(
                wizard.with_context(discount_date=wizard.payment_date).line_ids.mapped(
                    "move_id.has_discount_available"
                )
            )
            # If any invoice has force_financial_discount
            any_invoice_with_forced_discount = any(
                wizard.line_ids.mapped("move_id.force_financial_discount")
            )
            # Display the button only if there are invoices with late discounts
            wizard.show_force_financial_discount = (
                any_invoice_with_forced_discount
                or any_invoice_with_discount
                and not_all_invoices_with_discounts_available
            )

    @api.depends("with_financial_discount", "force_financial_discount")
    def _compute_from_lines(self):
        return super()._compute_from_lines()

    @api.depends(
        "with_financial_discount",
    )
    def _compute_amount(self):
        for wizard in self:
            if not wizard.with_financial_discount:
                super(AccountPaymentRegister, wizard)._compute_amount()
            else:
                wizard.amount = wizard._get_financial_discount_values_from_wizard()[
                    "amount"
                ]

    @api.depends("amount", "with_financial_discount")
    def _compute_payment_difference(self):
        super()._compute_payment_difference()
        for wizard in self:
            if wizard.with_financial_discount:
                wizard._onchange_payment_difference()

    @api.onchange("payment_difference")
    def _onchange_payment_difference(self):
        self.ensure_one()
        # Only override the writeoff configuration in case the wizard
        #  is not edited yet
        if self.with_financial_discount and isinstance(self.id, models.NewId):
            payment_difference = self.payment_difference
            financial_discount_values = (
                self._get_financial_discount_values_from_wizard()
            )
            if (
                payment_difference
                and float_compare(
                    financial_discount_values.get("amount_discount"),
                    payment_difference,
                    precision_rounding=self.currency_id.rounding,
                )
                == 0
            ):
                self.payment_difference_handling = financial_discount_values.get(
                    "payment_difference_handling"
                )
                self.writeoff_label = financial_discount_values.get("writeoff_label")
                self.writeoff_account_id = financial_discount_values.get(
                    "writeoff_account_id"
                )

    def _create_payment_vals_from_batch(self, batch_result):
        res = super()._create_payment_vals_from_batch(batch_result)
        if any(batch_result.get("lines").mapped("amount_discount")):
            financial_discount_values = self._get_financial_discount_values_from_batch(
                batch_result
            )
            lines_currency = self.env["res.currency"].browse(res.get("currency_id"))
            if lines_currency == self.company_id.currency_id:
                amount = financial_discount_values.get("amount")
                amount_discount = financial_discount_values.get("amount_discount")
            else:
                amount = financial_discount_values.get("amount_currency")
                amount_discount = financial_discount_values.get(
                    "amount_discount_currency"
                )
            payment_difference = res.get("amount") - amount
            res["amount"] = amount
            if (
                float_compare(
                    amount_discount,
                    payment_difference,
                    precision_rounding=lines_currency.rounding,
                )
                == 0
                and not self.currency_id.is_zero(payment_difference)
                and financial_discount_values.get("payment_difference_handling")
                == "reconcile"
            ):
                res["write_off_line_vals"] = {
                    "name": financial_discount_values.get("writeoff_label"),
                    "amount": amount_discount,
                    "account_id": financial_discount_values.get("writeoff_account_id"),
                }

        return res

    def _get_common_financial_discount_values(self):
        res = {
            # TODO As writeoff_label is not translatable, keep the string in english?
            #  We should probably move this somewhere so same label can be used
            #  from bank statement reconciliation?
            "writeoff_label": _("Financial Discount"),
            "payment_difference_handling": "reconcile",
        }
        if self.payment_type == "outbound":
            res[
                "writeoff_account_id"
            ] = self.company_id.financial_discount_revenue_account_id.id
        elif self.payment_type == "inbound":
            res[
                "writeoff_account_id"
            ] = self.company_id.financial_discount_expense_account_id.id
        return res

    def _get_financial_discount_values_from_batch(self, batch_result):
        self.ensure_one()
        res = self._get_common_financial_discount_values()
        res.update(self._get_financial_discount_amounts(batch_result))
        return res

    def _get_financial_discount_values_from_wizard(self):
        self.ensure_one()
        res = self._get_common_financial_discount_values()
        discount_amounts = self._get_financial_discount_amounts()
        if self.currency_id == self.source_currency_id:
            # Same currency.
            res["amount"] = discount_amounts.get("amount_currency")
            res["amount_discount"] = discount_amounts.get("amount_discount_currency")
        elif self.currency_id == self.company_id.currency_id:
            # Payment expressed on the company's currency.
            res["amount"] = discount_amounts.get("amount")
            res["amount_discount"] = discount_amounts.get("amount_discount")
        else:
            # Foreign currency on payment different than the one set on the journal entries.
            res["amount"] = self.source_currency_id._convert(
                discount_amounts.get("amount_currency"),
                self.currency_id,
                self.company_id,
                self.payment_date,
            )
            res["amount_discount"] = self.source_currency_id._convert(
                discount_amounts.get("amount_discount_currency"),
                self.currency_id,
                self.company_id,
                self.payment_date,
            )
        return res

    def _get_financial_discount_amounts(self, batch_result=None):
        if batch_result is None:
            invoice_lines = self.line_ids
            amount = self.source_amount
            amount_currency = self.source_amount_currency
            currency = self.source_currency_id
        else:
            invoice_lines = batch_result.get("lines")
            batch_values = self._get_wizard_values_from_batch(batch_result)
            amount_currency = batch_values.get("source_amount_currency")
            amount = batch_values.get("source_amount")
            currency = self.env["res.currency"].browse(
                batch_values.get("source_currency_id")
            )
        invoices = invoice_lines.mapped("move_id")
        query_res = invoices._financial_discount_query()
        date = self.payment_date or fields.Date.context_today()
        company = self.company_id
        amount_discount = 0
        amount_discount_currency = 0
        for res_line in query_res:
            if (
                not self.env.context.get("bypass_financial_discount")
                and res_line["date_discount"]
                and (
                    res_line["date_discount"] >= date
                    or res_line["force_financial_discount"]
                    or self.force_financial_discount
                )
            ):
                # TODO Check coverage on multicurrency test
                if (
                    res_line["currency_id"] == currency.id
                    and res_line["currency_id"] == company.currency_id.id
                ):
                    amount -= abs(res_line["amount_discount"])
                    amount_currency -= abs(res_line["amount_discount"])
                    amount_discount += abs(res_line["amount_discount"])
                    amount_discount_currency += abs(res_line["amount_discount"])
                else:
                    amount -= abs(res_line["amount_discount"])
                    amount_currency -= abs(res_line["amount_discount_currency"])
                    amount_discount += abs(res_line["amount_discount"])
                    amount_discount_currency += abs(
                        res_line["amount_discount_currency"]
                    )
        return {
            "amount": amount,
            "amount_currency": amount_currency,
            "amount_discount": amount_discount,
            "amount_discount_currency": amount_discount_currency,
        }
