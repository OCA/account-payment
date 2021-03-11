# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    "out_invoice": "customer",
    "out_refund": "customer",
    "in_invoice": "supplier",
    "in_refund": "supplier",
}

# Since invoice amounts are unsigned,
# this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    "out_invoice": 1,
    "in_refund": 1,
    "in_invoice": -1,
    "out_refund": -1,
}


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.onchange("payment_date")
    def onchange_payment_date(self):
        if self.payment_date:
            for rec in self.invoice_payments:
                rec.with_context(reset_autofill=True).onchange_amount()

    @api.onchange("invoice_payments")
    def _get_amount(self):
        total = 0.0
        for rec in self.invoice_payments:
            total += rec.amount
        if self.invoice_payments:
            self.cheque_amount = total

    def get_batch_payment_amount(self, invoice=None, payment_date=None):
        res = super().get_batch_payment_amount(invoice, payment_date)
        discount_information = (
            invoice.invoice_payment_term_id._check_payment_term_discount(
                invoice, payment_date
            )
        )
        discount_amt = discount_information[0]
        discount_account_id = discount_information[1]
        # compute payment difference
        payment_difference = self.payment_difference
        if payment_difference <= discount_amt:
            # Prepare val
            res.update(
                {
                    "payment_difference": discount_amt,
                    "amount": abs(invoice.amount_residual - discount_amt),
                    "payment_difference_handling": "reconcile",
                    "writeoff_account_id": discount_account_id,
                    "note": (payment_difference != 0.0)
                    and "Early Pay Discount"
                    or False,
                }
            )
        return res

    def get_invoice_payment_line(self, invoice):
        if invoice.discount_amt == 0.0:
            return super().get_invoice_payment_line(invoice)
        # Set payment date as today
        today = fields.Date.today()
        vals = self.get_batch_payment_amount(invoice, today)
        discount_information = (
            invoice.invoice_payment_term_id._check_payment_term_discount(invoice, today)
        )
        discount = discount_information[0]
        if discount_information[2]:
            amount = discount_information[2] - discount
        else:
            amount = invoice.amount_residual
        payment_difference = discount
        if amount <= 0.0:
            amount = vals.get("amt") or 0.0
        if discount <= 0.0:
            payment_difference = vals.get("payment_difference") or 0.0
        return (
            0,
            0,
            {
                "partner_id": invoice.partner_id.id,
                "invoice_id": invoice.id,
                "balance": invoice.amount_residual or 0.0,
                "amount": amount,
                "payment_difference_handling": vals.get(
                    "payment_difference_handling", False
                ),
                "payment_difference": payment_difference,
                "writeoff_account_id": vals.get("writeoff_account_id", False),
                "note": vals.get("note", False),
            },
        )

    def auto_fill_payments(self):
        # Check if payment date set
        if not self.payment_date:
            raise exceptions.ValidationError(_("Please enter the payment date."))
        return super().auto_fill_payments()
