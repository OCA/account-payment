# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaymentLine(models.Model):

    _inherit = "account.payment.line"

    def _prepare_account_payment_vals(self):
        """Prepare the dictionary to create an account payment record from a set of
        payment lines.
        """
        payment_vals = super()._prepare_account_payment_vals()

        epd_aml_values_list = []
        for rec in self:
            currency = rec.currency_id
            conversion_rate = rec.env["res.currency"]._get_conversion_rate(
                currency,
                rec.company_id.currency_id,
                rec.company_id,
                rec.date,
            )

            aml = rec.move_line_id
            date_for_discount = rec.date
            if rec.pay_with_discount:
                # force aml to be eligible for early payment_discount
                date_for_discount = aml.discount_date
                if (
                    aml._is_eligible_for_early_payment_discount(
                        currency, date_for_discount
                    )
                    or rec.pay_with_discount
                ):
                    epd_aml_values_list.append(
                        {
                            "aml": aml,
                            "amount_currency": -aml.amount_residual_currency,
                            "balance": aml.company_currency_id.round(
                                -aml.amount_residual_currency * conversion_rate
                            ),
                        }
                    )

                    # compute open amount
                    invoice = rec.move_line_id.move_id
                    refunds_amount_total = 0
                    sign = (
                        -1 if invoice.payment_mode_id.payment_type == "outbound" else 1
                    )
                    for invoice_line in invoice.line_ids:
                        # compute discount amount
                        if invoice_line.currency_id:
                            amount_of_discount = invoice_line.amount_residual_currency
                        else:
                            amount_of_discount = invoice_line.amount_residual

                        if invoice_line.move_id.is_invoice():
                            amount_of_discount *= -1

                        # apply discount
                        amount_of_discount *= 1 - (
                            invoice_line.discount_percentage / 100
                        )
                        refunds_amount_total += amount_of_discount

                    open_amount_currency = (
                        invoice.amount_residual - refunds_amount_total
                    ) * sign

                    open_balance = rec.company_id.currency_id.round(
                        open_amount_currency * conversion_rate
                    )
        if epd_aml_values_list:
            early_payment_values = rec.env[
                "account.move"
            ]._get_invoice_counterpart_amls_for_early_payment_discount(
                epd_aml_values_list, open_balance
            )
            payment_vals["write_off_line_vals"] = []

            for aml_values_list in early_payment_values.values():
                payment_vals["write_off_line_vals"] += aml_values_list

        return payment_vals
