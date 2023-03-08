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
        currency = self.currency_id
        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )

        epd_aml_values_list = []
        aml = self.move_line_id
        date_for_discount = self.date
        if self.pay_with_discount:
            # force aml to be eligible for early payment_discount
            date_for_discount = aml.discount_date
            if aml._is_eligible_for_early_payment_discount(currency, date_for_discount):
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
                invoice = self.move_line_id.move_id
                refunds_amount_total = 0
                sign = -1 if invoice.payment_mode_id.payment_type == "outbound" else 1
                for invoice_line in invoice.line_ids:
                    refunds_amount_total += (
                        invoice_line.discount_amount_currency
                    ) * sign

                open_amount_currency = (
                    invoice.amount_total - refunds_amount_total
                ) * sign

                open_balance = self.company_id.currency_id.round(
                    open_amount_currency * conversion_rate
                )
                early_payment_values = self.env[
                    "account.move"
                ]._get_invoice_counterpart_amls_for_early_payment_discount(
                    epd_aml_values_list, open_balance
                )
                payment_vals["write_off_line_vals"] = []
                for aml_values_list in early_payment_values.values():
                    payment_vals["write_off_line_vals"] += aml_values_list

        return payment_vals
