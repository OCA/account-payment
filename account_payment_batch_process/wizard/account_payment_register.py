# Copyright (C) 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
from odoo.tools.float_utils import float_compare

try:
    from num2words import num2words
except ImportError:
    logging.getLogger(__name__).warning(
        "The num2words python library is not installed."
    )
    num2words = None


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

    @api.depends("invoice_customer_payments.receiving_amt")
    def _compute_customer_pay_total(self):
        self.total_customer_pay_amount = sum(
            line.receiving_amt for line in self.invoice_customer_payments
        )

    @api.depends("invoice_payments.paying_amt")
    def _compute_pay_total(self):
        self.total_pay_amount = sum(line.paying_amt for line in self.invoice_payments)

    @api.depends("invoice_payments.balance_amt")
    def _compute_cheque_amount(self):
        self.cheque_amount = sum(line.balance_amt for line in self.invoice_payments)

    is_auto_fill = fields.Char(string="Auto-Fill Pay Amount")
    invoice_payments = fields.One2many(
        "invoice.payment.line", "wizard_id", string="Payments"
    )
    is_customer = fields.Boolean(string="Is Customer?")
    invoice_customer_payments = fields.One2many(
        "invoice.customer.payment.line", "wizard_id", string="Receipts"
    )
    cheque_amount = fields.Float(
        "Batch Payment Total",
        required=True,
        compute="_compute_cheque_amount",
        store=True,
        readonly=False,
    )
    total_pay_amount = fields.Float("Total Invoices:", compute="_compute_pay_total")
    total_customer_pay_amount = fields.Float(
        "Total Customer Invoices:", compute="_compute_customer_pay_total"
    )

    def get_invoice_customer_payments(self, invoice):
        payment_lines = []
        for inv in invoice:
            payment_lines.append(
                (
                    0,
                    0,
                    {
                        "partner_id": inv.partner_id.id,
                        "invoice_id": inv.id,
                        "balance_amt": inv.amount_residual or 0.0,
                        "receiving_amt": inv.amount_residual or 0.0,
                        "payment_difference": 0.0,
                        "payment_difference_handling": "reconcile",
                        "writeoff_account_id": inv.invoice_payment_term_id
                        and inv.invoice_payment_term_id.line_ids[
                            0
                        ].discount_income_account_id.id,
                    },
                )
            )

        return payment_lines

    def get_invoice_vendor_payments(self, invoice):
        payment_lines = []
        for inv in invoice:
            payment_lines.append(
                (
                    0,
                    0,
                    {
                        "partner_id": inv.partner_id.id,
                        "invoice_id": inv.id,
                        "balance_amt": inv.amount_residual or 0.0,
                        "paying_amt": inv.amount_residual or 0.0,
                        "payment_difference": 0.0,
                        "payment_difference_handling": "reconcile",
                        "writeoff_account_id": inv.invoice_payment_term_id
                        and inv.invoice_payment_term_id.line_ids[
                            0
                        ].discount_expense_account_id.id,
                    },
                )
            )

        return payment_lines

    @api.model
    def default_get(self, fields):
        # rec = {}
        if self.env.context and not self.env.context.get("batch", False):
            return super(AccountPaymentRegister, self).default_get(fields)
        rec = super(AccountPaymentRegister, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get("active_model")
        active_ids = context.get("active_ids")
        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _(
                    "The wizard is executed without "
                    "active_model or active_ids in the "
                    "context."
                )
            )
        if active_model != "account.move":
            raise UserError(
                _(
                    """The expected model for """
                    """this action is 'account.move', not '%s'."""
                )
                % active_model
            )
        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        if any(
            invoice.state != "posted"
            or invoice.payment_state not in ["not_paid", "partial"]
            for invoice in invoices
        ):
            raise UserError(
                _("""You can only register payments """ """for open invoices.""")
            )

        if any(inv.payment_mode_id != invoices[0].payment_mode_id for inv in invoices):
            raise UserError(
                _(
                    "You can only register a batch payment for"
                    "invoices with the same"
                    " payment mode."
                )
            )

        if any(
            MAP_INVOICE_TYPE_PARTNER_TYPE[inv.move_type]
            != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type]
            for inv in invoices
        ):
            raise UserError(
                _(
                    "You cannot mix customer invoices and vendor"
                    "bills in a single "
                    "payment."
                )
            )
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(
                _(
                    "In order to pay multiple bills at once, "
                    "they must use the same "
                    "currency."
                )
            )

        if "batch" in context and context.get("batch"):
            payment_lines = []
            if MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type] == "customer":
                payment_lines = self.get_invoice_customer_payments(invoices)
                rec.update(
                    {"invoice_customer_payments": payment_lines, "is_customer": True}
                )
            else:
                payment_lines = self.get_invoice_vendor_payments(invoices)
                rec.update({"invoice_payments": payment_lines, "is_customer": False})
        else:
            # Checks on received invoice records
            if any(
                MAP_INVOICE_TYPE_PARTNER_TYPE[inv.move_type]
                != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type]
                for inv in invoices
            ):
                raise UserError(
                    _(
                        "You cannot mix customer invoices and vendor"
                        "bills in a single"
                        " payment."
                    )
                )

        total_amount = sum(
            inv.amount_residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.move_type]
            for inv in invoices
        )
        rec.update(
            {
                "amount": abs(total_amount),
                "currency_id": invoices[0].currency_id.id,
                "payment_type": total_amount > 0 and "inbound" or "outbound",
                "partner_id": invoices[0].commercial_partner_id.id,
                "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type],
                "company_id": self.env.user.company_id,
            }
        )
        return rec

    def get_payment_batch_vals(self, inv_payment=False, group_data=None):
        if group_data:
            res = {
                "journal_id": self.journal_id.id,
                "payment_method_id": "payment_method_id" in group_data
                and group_data["payment_method_id"]
                or self.payment_method_id.id,
                "date": self.payment_date,
                "ref": group_data["memo"],
                "payment_type": self.payment_type,
                "amount": group_data["total"],
                "currency_id": self.currency_id.id,
                "partner_id": int(group_data["partner_id"]),
                "partner_type": group_data["partner_type"],
            }
            if self.payment_method_id == self.env.ref(
                "account_check_printing.account_payment_method_check"
            ):
                res.update(
                    {
                        "check_amount_in_words": group_data["total_chq_amt_in_words"]
                        or "",
                    }
                )
            return res

    def is_customer_make_payment(self, context):
        if float_compare(self.total_customer_pay_amount, self.cheque_amount, 2) != 0:
            raise ValidationError(
                _(
                    "The pay amount of the invoices and the batch"
                    "payment total do "
                    "not match."
                )
            )

    def is_vendor_make_payment(self, context):
        if float_compare(self.total_pay_amount, self.cheque_amount, 2) != 0:
            raise ValidationError(
                _(
                    "The pay amount of the invoices and the batch payment"
                    "total do"
                    " not match."
                )
            )

    def get_memo(self, memo, group_data, partner_id, data_get):
        if memo:
            memo = (
                group_data[partner_id]["memo"]
                + " : "
                + memo
                + "-"
                + str(data_get.invoice_id.name)
            )
        else:
            memo = (
                group_data[partner_id]["memo"] + " : " + str(data_get.invoice_id.name)
            )

        return memo

    def get_partner_amt_words(self, old_total, data_get):

        total_chq_amt_in_words = num2words(
            math.floor(old_total + data_get.receiving_amt)
        ).title()
        decimals = (old_total + data_get.receiving_amt) % 1
        if decimals >= 10 ** -2:
            total_chq_amt_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )

        return total_chq_amt_in_words

    def update_partner_inv_val(self, data_get, group_data, partner_id, name):
        inv_val = {
            "line_name": name,
            "receiving_amt": data_get.receiving_amt,
            "payment_difference_handling": data_get.payment_difference_handling,
            "payment_difference": data_get.payment_difference,
            "writeoff_account_id": data_get.writeoff_account_id
            and data_get.writeoff_account_id.id
            or False,
        }
        group_data[partner_id]["inv_val"].update({str(data_get.invoice_id.id): inv_val})

    def update_group_data(self, group_data, data_get, total_chq_amt_in_words):
        # build memo value
        if self.communication:
            memo = self.communication + "-" + str(data_get.invoice_id.name)
        else:
            memo = str(data_get.invoice_id.name)
        # prepare name
        partner_id = str(data_get.invoice_id.partner_id.id)
        name = ""
        if data_get.reason_code:
            name = str(data_get.reason_code.code)
        if data_get.note:
            name = name + ": " + str(data_get.note)
        if not name:
            name = "Counterpart"
        inv_val = {
            str(data_get.invoice_id.id): {
                "line_name": name,
                "receiving_amt": data_get.receiving_amt,
                "payment_difference_handling": data_get.payment_difference_handling,
                "payment_difference": data_get.payment_difference,
                "writeoff_account_id": data_get.writeoff_account_id
                and data_get.writeoff_account_id.id
                or False,
            }
        }
        group_data.update(
            {
                partner_id: {
                    "partner_id": partner_id,
                    "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                        data_get.invoice_id.move_type
                    ],
                    "total": data_get.receiving_amt,
                    "payment_method_id": data_get.payment_method_id
                    and data_get.payment_method_id.id
                    or False,
                    "total_chq_amt_in_words": total_chq_amt_in_words,
                    "memo": memo,
                    "temp_invoice": data_get.invoice_id.id,
                    "inv_val": inv_val,
                }
            }
        )

    def get_rec_amt_words(self, data_get):
        total_chq_amt_in_words = num2words(
            math.floor(math.floor(data_get.receiving_amt))
        ).title()
        decimals = data_get.receiving_amt % 1
        if decimals >= 10 ** -2:
            total_chq_amt_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )

        return total_chq_amt_in_words

    def get_customer_receiving_amt(self, memo, group_data, data_get):

        data_get.payment_difference = data_get.balance_amt - data_get.receiving_amt
        if data_get.payment_difference_handling:
            data_get.invoice_id.discount_taken = data_get.payment_difference
        partner_id = str(data_get.invoice_id.partner_id.id)
        if partner_id in group_data:
            old_total = group_data[partner_id]["total"]
            # build memo value
            memo = self.get_memo(memo, group_data, partner_id, data_get)
            # calculate amount in words
            total_chq_amt_in_words = self.get_partner_amt_words(old_total, data_get)
            # prepare name
            name = ""
            if data_get.reason_code:
                name = str(data_get.reason_code.code)
            if data_get.note:
                name = name + ": " + str(data_get.note)
            if not name:
                name = "Counterpart"
            group_data[partner_id].update(
                {
                    "partner_id": partner_id,
                    "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                        data_get.invoice_id.move_type
                    ],
                    "total": old_total + data_get.receiving_amt,
                    "memo": memo,
                    "temp_invoice": data_get.invoice_id.id,
                    "payment_method_id": data_get.payment_method_id
                    and data_get.payment_method_id.id
                    or False,
                    "total_chq_amt_in_words": total_chq_amt_in_words,
                }
            )
            self.update_partner_inv_val(data_get, group_data, partner_id, name)

        else:
            # calculate amount in words
            total_chq_amt_in_words = self.get_rec_amt_words(data_get)
            self.update_group_data(group_data, data_get, total_chq_amt_in_words)

    def update_partner_inv(self, partner_invoices, data_get):
        invoices = (
            partner_invoices
            and partner_invoices[data_get.invoice_id.partner_id.id]
            or []
        )
        invoices.append(data_get.invoice_id.id)
        partner_invoices.update({data_get.invoice_id.partner_id.id: invoices})

        return partner_invoices

    def total_pay_p_amt_in_words(self, old_total, data_get):
        total_chq_amt_in_words = num2words(
            math.floor(old_total + data_get.paying_amt)
        ).title()
        decimals = (old_total + data_get.paying_amt) % 1

        if decimals >= 10 ** -2:
            total_chq_amt_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )
        return total_chq_amt_in_words

    def total_pay_amt_in_words(self, data_get):
        total_chq_amt_in_words = num2words(math.floor(data_get.paying_amt)).title()
        decimals = (data_get.paying_amt) % 1

        if decimals >= 10 ** -2:
            total_chq_amt_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )

    def get_pay_inv_val(self, name, data_get):
        inv_val = {
            "line_name": name,
            "paying_amt": data_get.paying_amt,
            "payment_difference_handling": data_get.payment_difference_handling,
            "payment_difference": data_get.payment_difference,
            "writeoff_account_id": data_get.writeoff_account_id
            and data_get.writeoff_account_id.id
            or False,
        }
        return inv_val

    def update_group_pay_data(
        self, partner_id, group_data, data_get, total_chq_amt_in_words
    ):
        # build memo value
        if self.communication:
            memo = self.communication + "-" + str(data_get.invoice_id.name)
        else:
            memo = str(data_get.invoice_id.name)
        name = ""
        if data_get.reason_code:
            name = str(data_get.reason_code.code)
        if data_get.note:
            name = name + ": " + str(data_get.note)
        if not name:
            name = "Counterpart"
        inv_val = {
            "line_name": name,
            "paying_amt": data_get.paying_amt,
            "payment_difference_handling": data_get.payment_difference_handling,
            "payment_difference": data_get.payment_difference,
            "writeoff_account_id": data_get.writeoff_account_id
            and data_get.writeoff_account_id.id
            or False,
        }
        group_data.update(
            {
                partner_id: {
                    "partner_id": partner_id,
                    "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                        data_get.invoice_id.move_type
                    ],
                    "total": data_get.paying_amt,
                    "total_check_amount_in_words": total_chq_amt_in_words,
                    "memo": memo,
                    "temp_invoice": data_get.invoice_id.id,
                    "inv_val": {str(data_get.invoice_id.id): inv_val},
                }
            }
        )

    def get_paying_amt(self, memo, group_data, data_get):

        data_get.payment_difference = data_get.balance_amt - data_get.paying_amt
        if data_get.payment_difference_handling:
            data_get.invoice_id.discount_taken = data_get.payment_difference
        partner_id = str(data_get.invoice_id.partner_id.id)
        if partner_id in group_data:
            old_total = group_data[partner_id]["total"]
            # build memo value
            if self.communication:
                memo = (
                    group_data[partner_id]["memo"]
                    + " : "
                    + self.communication
                    + "-"
                    + str(data_get.invoice_id.name)
                )
            else:
                memo = (
                    group_data[partner_id]["memo"]
                    + " : "
                    + str(data_get.invoice_id.name)
                )
            # Calculate amount in words
            total_chq_amt_in_words = self.total_pay_p_amt_in_words(old_total, data_get)
            group_data[partner_id].update(
                {
                    "partner_id": partner_id,
                    "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                        data_get.invoice_id.move_type
                    ],
                    "total": old_total + data_get.paying_amt,
                    "memo": memo,
                    "temp_invoice": data_get.invoice_id.id,
                    "total_chq_amt_in_words": total_chq_amt_in_words,
                }
            )
            # prepare name
            name = ""
            if data_get.reason_code:
                name = str(data_get.reason_code.code)
            if data_get.note:
                name = name + ": " + str(data_get.note)
            if not name:
                name = "Counterpart"
            # Update with payment diff data

            inv_val = self.get_pay_inv_val(name, data_get)
            group_data[partner_id]["inv_val"].update(
                {str(data_get.invoice_id.id): inv_val}
            )
        else:
            # calculate amount in words
            total_chq_amt_in_words = self.total_pay_amt_in_words(data_get)
            # prepare name
            self.update_group_pay_data(
                partner_id, group_data, data_get, total_chq_amt_in_words
            )

    def make_payments(self):
        # Make group data either for Customers or Vendors
        context = dict(self._context or {})
        group_data = {}
        memo = self.communication or " "
        partner_invoices = {}
        if self.is_customer:
            context.update({"is_customer": True})
            self.is_customer_make_payment(context)
            for data_get in self.invoice_customer_payments:
                partner_invoices = self.update_partner_inv(partner_invoices, data_get)
                if data_get.receiving_amt > 0:
                    self.get_customer_receiving_amt(memo, group_data, data_get)
        else:
            context.update({"is_customer": False})
            self.is_vendor_make_payment(context)
            for data_get in self.invoice_payments:
                partner_invoices = self.update_partner_inv(partner_invoices, data_get)
                if data_get.paying_amt > 0:
                    # Get difference amt
                    self.get_paying_amt(memo, group_data, data_get)

        # update context
        context.update({"group_data": group_data})
        # making partner wise payment
        payment_ids = []
        for partner in list(group_data):
            # update active_ids with active invoice id
            if context.get("active_ids", False) and group_data[partner].get(
                "temp_invoice", False
            ):
                context.update({"active_ids": group_data[partner]["temp_invoice"]})
            self.get_payment_batch_vals(group_data=group_data[partner])

            payment = (
                self.env["account.payment"]
                .with_context(context)
                .create(self.get_payment_batch_vals(group_data=group_data[partner]))
            )
            payment_ids.append(payment.id)
            payment.action_post()

            # Reconciliation
            domain = [
                ("account_internal_type", "in", ("receivable", "payable")),
                ("reconciled", "=", False),
            ]
            payment_lines = payment.line_ids.filtered_domain(domain)
            invoices = self.env["account.move"].browse(partner_invoices[int(partner)])
            lines = invoices.line_ids.filtered_domain(domain)
            for account in payment_lines.account_id:
                (payment_lines + lines).filtered_domain(
                    [("account_id", "=", account.id), ("reconciled", "=", False)]
                ).reconcile()

        view_id = self.env["ir.model.data"].get_object_reference(
            "account_payment_batch_process",
            "view_account_supplier_payment_tree_nocreate",
        )[1]
        return {
            "name": _("Payments"),
            "view_type": "form",
            "view_mode": "tree",
            "res_model": "account.payment",
            "view_id": view_id,
            "type": "ir.actions.act_window",
            "target": "new",
            "domain": "[('id','in',%s)]" % (payment_ids),
            "context": {"group_by": "partner_id"},
        }

    def get_inv_customer_paymts_rming_amt(self, remaining_amt, count):
        for payline in self.invoice_customer_payments:
            if remaining_amt < 0.0:
                break
            amount = sum(line.balance_amt for line in self.invoice_customer_payments)
            count += 1
            if count <= len(self.invoice_customer_payments):
                payline.write(
                    {
                        "receiving_amt": 0.0,
                        "payment_difference": amount,
                    }
                )
                if (
                    remaining_amt >= payline.balance_amt
                    and not remaining_amt == payline.balance_amt
                ):
                    payline.write(
                        {
                            "receiving_amt": payline.balance_amt,
                            "payment_difference": amount,
                        }
                    )
                    remaining_amt -= payline.balance_amt
                elif remaining_amt > 0.0:
                    if payline.payment_difference != 0.0:
                        payline.write(
                            {
                                "receiving_amt": remaining_amt,
                                "payment_difference": amount,
                            }
                        )
                    remaining_amt -= payline.balance_amt
                elif remaining_amt <= payline.balance_amt:
                    payline.write(
                        {
                            "receiving_amt": self.cheque_amount,
                            "payment_difference": amount,
                        }
                    )
                    remaining_amt -= payline.balance_amt

            return remaining_amt

    def get_inv_paymts_rming_amt(self, remaining_amt, count):
        for payline in self.invoice_payments:
            if remaining_amt < 0.0:
                break
            amount = sum(line.balance_amt for line in self.invoice_payments)
            count += 1
            if count <= len(self.invoice_payments):
                payline.write(
                    {
                        "paying_amt": 0.0,
                        "payment_difference": amount,
                    }
                )
                if (
                    remaining_amt >= payline.balance_amt
                    and not remaining_amt == payline.balance_amt
                ):
                    payline.write(
                        {
                            "paying_amt": payline.balance_amt,
                            "payment_difference": amount,
                        }
                    )
                    remaining_amt -= payline.balance_amt
                elif remaining_amt > 0.0:
                    if payline.payment_difference != 0.0:
                        payline.write(
                            {
                                "paying_amt": remaining_amt,
                                "payment_difference": amount,
                            }
                        )
                    remaining_amt -= payline.balance_amt
                elif remaining_amt <= payline.balance_amt:
                    payline.write(
                        {
                            "paying_amt": self.cheque_amount,
                            "payment_difference": amount,
                        }
                    )
                    remaining_amt -= payline.balance_amt

            return remaining_amt

    def auto_fill_payments(self):
        ctx = self._context.copy()
        batch_payment = self.cheque_amount
        remaining_amt = batch_payment
        count = 0
        for wiz in self:
            if wiz.is_customer:
                if wiz.invoice_customer_payments:
                    wiz.get_inv_customer_paymts_rming_amt(remaining_amt, count)
                    ctx.update(
                        {
                            "reference": wiz.communication or "",
                            "journal_id": wiz.journal_id.id,
                        }
                    )
            else:
                if wiz.invoice_payments:
                    wiz.get_inv_paymts_rming_amt(remaining_amt, count)
                    ctx.update(
                        {
                            "reference": wiz.communication or "",
                            "journal_id": wiz.journal_id.id,
                        }
                    )
        return {
            "name": _("Batch Payments"),
            "view_mode": "form",
            "view_id": False,
            "res_id": self.id,
            "res_model": "account.payment.register",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
            "context": ctx,
        }
