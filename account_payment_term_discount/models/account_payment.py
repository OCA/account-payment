# Copyright 2018 Open Source Integrators (http://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
    )
    discount_amt = fields.Monetary(store=True)

    @api.model
    def default_get(self, fields):
        res = super(AccountPaymentRegister, self).default_get(fields)
        # invoice_defaults = self.resolve_2many_commands('invoice_id',
        #                                                res.get('invoice_id'))
        active_ids = self.env.context.get("active_ids", [])
        if active_ids and len(active_ids) == 1:
            record = self.env["account.move"].browse(active_ids)
            res["invoice_id"] = record.id
            res["discount_amt"] = record.discount_amt
        return res

    @api.onchange("amount", "payment_difference", "payment_date", "group_payment")
    def onchange_payment_amount(self):
        self.payment_difference_handling = "open"
        self.writeoff_account_id = False
        self.writeoff_label = False
        total_payment_difference = 0.0
        payment_date = fields.Date.from_string(self.payment_date)

        # Single Invoice Payment or Grouped Payments
        if self.invoice_id or self.group_payment:
            for invoice in self.line_ids:
                if (
                    invoice.move_id
                    and invoice.move_id.invoice_payment_term_id
                    and invoice.move_id.invoice_payment_term_id.is_discount
                    and invoice.move_id.invoice_payment_term_id.line_ids
                ):
                    invoice_date = fields.Date.from_string(invoice.move_id.invoice_date)
                    discount_amt = invoice.move_id.discount_amt

                    for line in invoice.move_id.invoice_payment_term_id.line_ids:
                        payment_difference = total_payment_difference
                        # Check payment date discount validation
                        till_discount_date = invoice_date + relativedelta(
                            days=line.discount_days
                        )

                        if payment_date <= till_discount_date:
                            # changing payment date
                            if not payment_difference and discount_amt:
                                total_payment_difference += discount_amt
                                self.payment_difference_handling = "reconcile"
                                self.writeoff_account_id = (
                                    line.discount_expense_account_id.id
                                )
                                self.writeoff_label = "Payment Discount"

                            # customer is paying more
                            elif abs(payment_difference) < discount_amt:
                                total_payment_difference += abs(payment_difference)
                                self.payment_difference_handling = "reconcile"
                                self.writeoff_account_id = (
                                    line.discount_expense_account_id.id
                                )
                                self.writeoff_label = "Payment Discount"

                            # customer paying more than discount_amt
                            elif abs(payment_difference) > discount_amt:
                                total_payment_difference += abs(payment_difference)
                                self.payment_difference_handling = "open"
                                self.writeoff_label = False

                            # customer paying more than discount_amt
                            elif (
                                abs(payment_difference) == discount_amt
                                and discount_amt > 0
                            ):
                                total_payment_difference += abs(payment_difference)
                                self.payment_difference_handling = "reconcile"
                                self.writeoff_account_id = (
                                    line.discount_expense_account_id.id
                                )
                                self.writeoff_label = "Payment Discount"
                        else:
                            total_payment_difference += payment_difference

            self.discount_amt = total_payment_difference
            self.payment_difference = total_payment_difference
            self.amount = self.source_amount - total_payment_difference

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        for payment in self:
            if payment.payment_difference_handling == "reconcile":
                if len(payment.line_ids) == 1:
                    payment.invoice_id.write(
                        {
                            "discount_taken": abs(payment.payment_difference),
                            "discount_amt": 0,
                        }
                    )
                else:
                    for invoice in payment.line_ids:
                        invoice.move_id.write(
                            {
                                "discount_taken": invoice.move_id.discount_amt,
                                "discount_amt": 0,
                            }
                        )
        return res
