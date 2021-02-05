# Copyright (C) 2019, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round

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


class InvoicePaymentLine(models.TransientModel):
    _name = "invoice.payment.line"
    _description = "Invoice Payment Line"
    _rec_name = "invoice_id"

    @api.depends("paying_amt")
    def _compute_payment_difference(self):
        for rec in self:
            rec.payment_difference = rec.balance_amt - rec.paying_amt

    invoice_id = fields.Many2one(
        "account.move", string="Supplier Invoice", required=True
    )
    partner_id = fields.Many2one("res.partner", string="Supplier Name", required=True)
    balance_amt = fields.Float("Balance Amount", required=True)
    wizard_id = fields.Many2one("account.payment.register", string="Wizard")
    paying_amt = fields.Float("Pay Amount", required=True)
    check_amount_in_words = fields.Char(string="Amount in Words")
    payment_difference = fields.Float(
        compute="_compute_payment_difference", string="Difference Amount"
    )
    payment_difference_handling = fields.Selection(
        [("open", "Keep open"), ("reconcile", "Mark invoice as fully paid")],
        default="open",
        string="Action",
        copy=False,
    )
    writeoff_account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain=[("deprecated", "!=", True)],
        copy=False,
    )
    reason_code = fields.Many2one("payment.adjustment.reason", string="Reason Code")
    note = fields.Text("Note")

    @api.onchange("paying_amt")
    def _onchange_amount(self):
        check_amount_in_words = num2words(
            math.floor(self.paying_amt), lang="en"
        ).title()
        decimals = self.paying_amt % 1
        if decimals >= 10 ** -2:
            check_amount_in_words += _(" and %s/100") % str(
                int(round(float_round(decimals * 100, precision_rounding=1)))
            )
        self.check_amount_in_words = check_amount_in_words
        self.payment_difference = self.balance_amt - self.paying_amt

    @api.onchange("invoice_id")
    def _onchange_invoice_id(self):
        """
        Raise warning while the invoice is changed.
        """
        raise ValidationError(_("Invoice is unchangeable!"))

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """
        Raise warning while the Customer is changed.
        """
        raise ValidationError(_("Customer is unchangeable!"))

    @api.onchange("balance_amt")
    def _onchange_balance_amt(self):
        """
        Raise warning while the Balance Amount is changed.
        """
        raise ValidationError(_("Balance is unchangeable!"))
