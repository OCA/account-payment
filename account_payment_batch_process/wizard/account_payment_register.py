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

    @api.depends("invoice_payments.amount")
    def _compute_total(self):
        self.total_amount = sum(line.amount for line in self.invoice_payments)

    @api.depends("invoice_payments.balance")
    def _compute_cheque_amount(self):
        self.cheque_amount = sum(line.balance for line in self.invoice_payments)

    is_auto_fill = fields.Char(string="Auto-Fill Pay Amount")
    invoice_payments = fields.One2many(
        "invoice.payment.line", "wizard_id", string="Payments"
    )
    is_customer = fields.Boolean(string="Is Customer?")
    cheque_amount = fields.Float(
        "Batch Payment Total",
        required=True,
        compute="_compute_cheque_amount",
        store=True,
        readonly=False,
    )
    total_amount = fields.Float("Total Invoices:", compute="_compute_total")

    def get_invoice_payment_line(self, invoice):
        return (
            0,
            0,
            {
                "partner_id": invoice.partner_id.id,
                "invoice_id": invoice.id,
                "balance": invoice.amount_residual or 0.0,
                "amount": invoice.amount_residual or 0.0,
                "payment_difference": 0.0,
                "payment_difference_handling": "reconcile",
                "note": "Payment of invoice %s" % invoice.name,
            },
        )

    def get_invoice_payments(self, invoices):
        res = []
        for invoice in invoices:
            res.append(self.get_invoice_payment_line(invoice))
        return res

    @api.model
    def default_get(self, fields_list):
        if self.env.context and not self.env.context.get("batch", False):
            return super().default_get(fields_list)
        res = super().default_get(fields_list)
        context = dict(self._context or {})
        active_model = context.get("active_model")
        active_ids = context.get("active_ids")
        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _(
                    "The wizard is executed without active_model or active_ids in the context."
                )
            )
        if active_model != "account.move":
            raise UserError(
                _("The expected model for this action is 'account.move', not '%s'.")
                % active_model
            )
        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        if any(
            invoice.state != "posted"
            or invoice.payment_state not in ["not_paid", "partial"]
            for invoice in invoices
        ):
            raise UserError(_("You can only register payments for open invoices."))

        if any(inv.payment_mode_id != invoices[0].payment_mode_id for inv in invoices):
            raise UserError(
                _(
                    "You can only register a batch payment for"
                    " invoices with the same payment mode."
                )
            )
        if any(
            MAP_INVOICE_TYPE_PARTNER_TYPE[inv.move_type]
            != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type]
            for inv in invoices
        ):
            raise UserError(
                _(
                    "You cannot mix customer invoices and vendor bills in a single payment."
                )
            )
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(
                _(
                    "In order to pay multiple bills at once, they must use the same currency."
                )
            )

        if "batch" in context and context.get("batch"):
            is_customer = (
                MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type] == "customer"
            )
            payment_lines = self.get_invoice_payments(invoices)
            res.update({"invoice_payments": payment_lines, "is_customer": is_customer})
        else:
            # Checks on received invoice records
            if any(
                MAP_INVOICE_TYPE_PARTNER_TYPE[inv.move_type]
                != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type]
                for inv in invoices
            ):
                raise UserError(
                    _(
                        "You cannot mix customer invoices and vendor bills in a single payment."
                    )
                )

        total_amount = sum(
            inv.amount_residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.move_type]
            for inv in invoices
        )
        date_format = self.env["res.lang"]._lang_get(self.env.user.lang).date_format
        communication = "Batch payment of %s" % fields.Date.today().strftime(
            date_format
        )
        res.update(
            {
                "amount": abs(total_amount),
                "currency_id": invoices[0].currency_id.id,
                "payment_type": is_customer and "outbound" or "inbound",
                "partner_id": invoices[0].commercial_partner_id.id,
                "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type],
                "company_id": self.env.user.company_id,
                "communication": communication,
            }
        )
        return res

    def get_payment_values(self, group_data=None):
        res = {}
        if group_data:
            writeoff_amount = 0
            writeoff_account_id = False
            writeoff_name = False
            for invoice_id in list(group_data["inv_val"]):
                values = group_data["inv_val"][invoice_id]
                if (
                    self.currency_id
                    and not self.currency_id.is_zero(values["payment_difference"])
                    and values["payment_difference_handling"] == "reconcile"
                ):
                    writeoff_name = writeoff_name or values["line_name"]
                    writeoff_account_id = (
                        writeoff_account_id or values["writeoff_account_id"]
                    )
                    writeoff_amount += values["payment_difference"]
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
                "check_amount_in_words": group_data["check_amount_in_words"],
                "write_off_line_vals": {
                    "name": writeoff_name,
                    "account_id": writeoff_account_id,
                    "amount": writeoff_amount,
                },
            }
        return res

    def _check_amounts(self):
        if float_compare(self.total_amount, self.cheque_amount, 2) != 0:
            raise ValidationError(
                _(
                    "The pay amount of the invoices and the batch payment total do not match."
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

    def total_amount_in_words(self, data_get, old_total=0):
        check_amount_in_words = num2words(
            math.floor(old_total + data_get.amount)
        ).title()
        decimals = (old_total + data_get.amount) % 1
        if decimals >= 10 ** -2:
            check_amount_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )
        return check_amount_in_words

    def get_payment_invoice_value(self, name, data_get):
        return {
            "line_name": name,
            "amount": data_get.amount,
            "payment_difference_handling": data_get.payment_difference_handling,
            "payment_difference": data_get.payment_difference,
            "writeoff_account_id": data_get.writeoff_account_id
            and data_get.writeoff_account_id.id
            or False,
        }

    def update_group_pay_data(
        self, partner_id, group_data, data_get, check_amount_in_words
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
            "amount": data_get.amount,
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
                    "total": data_get.amount,
                    "check_amount_in_words": check_amount_in_words,
                    "memo": memo,
                    "temp_invoice": data_get.invoice_id.id,
                    "inv_val": {data_get.invoice_id.id: inv_val},
                }
            }
        )

    def get_amount(self, memo, group_data, line):
        line.payment_difference = line.balance - line.amount
        partner_id = line.invoice_id.partner_id.id
        if partner_id in group_data:
            old_total = group_data[partner_id]["total"]
            # build memo value
            if self.communication:
                memo = (
                    group_data[partner_id]["memo"]
                    + " : "
                    + self.communication
                    + "-"
                    + str(line.invoice_id.name)
                )
            else:
                memo = (
                    group_data[partner_id]["memo"] + " : " + str(line.invoice_id.name)
                )
            # Calculate amount in words
            check_amount_in_words = self.total_amount_in_words(line, old_total)
            group_data[partner_id].update(
                {
                    "partner_id": partner_id,
                    "partner_type": MAP_INVOICE_TYPE_PARTNER_TYPE[
                        line.invoice_id.move_type
                    ],
                    "total": old_total + line.amount,
                    "memo": memo,
                    "temp_invoice": line.invoice_id.id,
                    "check_amount_in_words": check_amount_in_words,
                }
            )
            # prepare name
            name = ""
            if line.reason_code:
                name = str(line.reason_code.code)
            if line.note:
                name = name + ": " + str(line.note)
            if not name:
                name = "Counterpart"
            # Update with payment diff data
            inv_val = self.get_payment_invoice_value(name, line)
            group_data[partner_id]["inv_val"].update({line.invoice_id.id: inv_val})
        else:
            # calculate amount in words
            check_amount_in_words = self.total_amount_in_words(line, 0)
            # prepare name
            self.update_group_pay_data(
                partner_id, group_data, line, check_amount_in_words
            )

    def _reconcile_open_invoices(
        self,
        line,
        inv,
        amount_residual,
        amount_residual_currency,
        reconciled,
        amount,
        debit_amount_currency,
        credit_amount_currency,
    ):
        acc_part_recnc_obj = self.env["account.partial.reconcile"]
        line.update(
            {
                "amount_residual": amount_residual,
                "amount_residual_currency": amount_residual_currency,
                "reconciled": reconciled,
            }
        )
        if inv.move_type == "out_invoice":
            part_rec_domain = [("debit_move_id", "=", line.id)]
        elif inv.move_type == "in_invoice":
            part_rec_domain = [("credit_move_id", "=", line.id)]
        partial = acc_part_recnc_obj.search(part_rec_domain, limit=1)
        if partial:
            partial.update(
                {
                    "amount": amount,
                    "debit_amount_currency": debit_amount_currency,
                    "credit_amount_currency": credit_amount_currency,
                }
            )

    def make_payments(self):
        # Make group data either for Customers or Vendors
        context = dict(self._context or {})
        group_data = {}
        memo = self.communication or " "
        context.update({"is_customer": self.is_customer})
        self._check_amounts()
        for invoice_payment_line in self.invoice_payments:
            if invoice_payment_line.amount > 0:
                self.get_amount(memo, group_data, invoice_payment_line)
        # update context
        context.update({"group_data": group_data})
        # making partner wise payment
        payment_ids = []
        for partner in list(group_data):
            # update active_ids with active invoice ids
            if context.get("active_ids", False) and group_data[partner].get(
                "inv_val", False
            ):
                context.update({"active_ids": list(group_data[partner]["inv_val"])})
            payment = (
                self.env["account.payment"]
                .with_context(context)
                .create(self.get_payment_values(group_data=group_data[partner]))
            )
            payment_ids.append(payment.id)
            payment.action_post()
            # Reconciliation
            domain = [
                ("account_internal_type", "in", ("receivable", "payable")),
                ("reconciled", "=", False),
            ]
            payment_lines = payment.line_ids.filtered_domain(domain)
            invoices = self.env["account.move"].browse(context.get("active_ids"))
            lines = invoices.line_ids.filtered_domain(domain)
            for account in payment_lines.account_id:
                (payment_lines + lines).filtered_domain(
                    [("account_id", "=", account.id), ("reconciled", "=", False)]
                ).reconcile()
            if any(
                group_data[partner]["inv_val"][inv.id]["payment_difference_handling"]
                == "open"
                for inv in invoices
            ):
                for inv in invoices:
                    if (
                        group_data[partner]["inv_val"][inv.id][
                            "payment_difference_handling"
                        ]
                        == "open"
                    ):
                        payment_state = "partial"
                    else:
                        payment_state = "paid"
                    for line in inv.line_ids:
                        if line.amount_residual > 0 and payment_state == "paid":
                            line_amount = 0.0
                            partial_amount = group_data[partner]["inv_val"][inv.id][
                                "amount"
                            ]
                            self._reconcile_open_invoices(
                                line,
                                inv,
                                line_amount,
                                line_amount,
                                True,
                                partial_amount,
                                partial_amount,
                                partial_amount,
                            )
                            continue
                        if line.reconciled and payment_state == "partial":
                            line_amount = group_data[partner]["inv_val"][inv.id][
                                "payment_difference"
                            ]
                            partial_amount = group_data[partner]["inv_val"][inv.id][
                                "amount"
                            ]
                            self._reconcile_open_invoices(
                                line,
                                inv,
                                line_amount,
                                line_amount,
                                False,
                                partial_amount,
                                partial_amount,
                                partial_amount,
                            )
                            continue
                    inv.update(
                        {
                            "payment_state": payment_state,
                            "amount_residual": group_data[partner]["inv_val"][inv.id][
                                "payment_difference"
                            ],
                            "amount_residual_signed": group_data[partner]["inv_val"][
                                inv.id
                            ]["payment_difference"],
                        }
                    )
                    inv._compute_payments_widget_reconciled_info()

        view_id = self.env["ir.model.data"].get_object_reference(
            "account_payment_batch_process",
            "view_account_payment_tree_nocreate",
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

    def get_batch_payment_amount(self, invoice=None, payment_date=None):
        return {
            "amount": False,
            "payment_difference": False,
            "payment_difference_handling": False,
            "writeoff_account_id": False,
        }

    def get_invoice_payments_remaining_amount(self, remaining_amount, count):
        total = 0.0
        for payline in self.invoice_payments:
            vals = self.get_batch_payment_amount(payline.invoice_id, self.payment_date)
            if remaining_amount < 0.0:
                break
            amount = vals.get("amt", False) or payline.balance
            total += amount
            payline.write(
                {
                    "amount": vals.get("amount", False) or payline.balance,
                    "payment_difference": vals.get("payment_difference", False) or 0.0,
                    "writeoff_account_id": vals.get("writeoff_account_id", False),
                    "payment_difference_handling": vals.get(
                        "payment_difference_handling", False
                    )
                    or "open",
                    "note": vals.get("note", False),
                }
            )
        self.cheque_amount = total

    def auto_fill_payments(self):
        ctx = self._context.copy()
        batch_payment = self.cheque_amount
        remaining_amt = batch_payment
        count = 0
        for wizard in self:
            if wizard.invoice_payments:
                wizard.get_invoice_payments_remaining_amount(remaining_amt, count)
            ctx.update(
                {
                    "reference": wizard.communication or "",
                    "journal_id": wizard.journal_id.id,
                }
            )
        return {
            "name": _("Batch Payments"),
            "view_mode": "form",
            "view_id": False,
            "view_type": "form",
            "res_id": self.id,
            "res_model": "account.payment.register",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
            "context": ctx,
        }
