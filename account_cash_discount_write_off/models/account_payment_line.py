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

        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            self.currency_id,
            self.company_currency_id,
            self.company_id,
            payment_vals["date"],
        )

        epd_aml_values_list = []
        for rec in self:
            if rec.pay_with_discount:
                aml = rec.move_line_id
                epd_aml_values_list.append(
                    {
                        "aml": aml,
                        "amount_currency": -aml.amount_residual_currency,
                        "balance": aml.company_currency_id.round(
                            -aml.amount_residual_currency * conversion_rate
                        ),
                    }
                )

        open_balance = self._get_open_balance(conversion_rate)

        if epd_aml_values_list:
            early_payment_values = rec.env[
                "account.move"
            ]._get_invoice_counterpart_amls_for_early_payment_discount(
                epd_aml_values_list, open_balance
            )
            payment_vals["write_off_line_vals"] = []
            for r in early_payment_values.values():
                payment_vals["write_off_line_vals"] += r

        return payment_vals

    def _get_open_balance(self, conversion_rate):
        open_balance = 0
        for invoice in self.mapped("move_line_id").mapped("move_id"):
            payment_sign = (
                -1 if invoice.payment_mode_id.payment_type == "outbound" else 1
            )
            # compute open amount
            refunds_amount_total = 0
            sign = -1 if invoice.is_outbound() else 1
            for invoice_line in invoice.line_ids:
                # compute discount amount
                amount_of_discount = sign * invoice_line.amount_residual_currency
                amount_of_discount *= 1 - (invoice_line.discount_percentage / 100)
                refunds_amount_total += amount_of_discount

            open_amount_currency = (
                invoice.amount_residual - refunds_amount_total
            ) * payment_sign

            open_balance += self.company_currency_id.round(
                open_amount_currency * conversion_rate
            )
        return open_balance
