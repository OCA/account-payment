# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from odoo import models, fields
from odoo.addons.payment_taler.utils.utils import generate_qr, generate_UUID, get_datetime_date_to_epoch
from odoo.addons.payment_taler.models.taler_api_methods import requestGetToken, postPlaceOrderWithFulfillmentMessage


class TalerInvoicing(models.Model):
    _inherit = 'account.move'
    # Because this model inherits, and does not have its own name, there is no need for it to appear in ir.model.access.csv
    # It will inherit the ir security settings from the account.move model

    is_taler_invoice = fields.Boolean(default=False) # This value is used in the xml file for invoices. If true, the invoice will contain the Taler QR Code

    taler_order_id = fields.Char(string="Taler order ID", default="")
    taler_order_url = fields.Char(string="Taler order URL", default="")
    taler_order_uri = fields.Char(string="Taler order URI", default="")
    taler_qr = fields.Char(string="Taler QR")

    # For an explanation on this field, see the equivalent field in model TalerTransaction
    taler_uuid = fields.Char(string="Taler UUID", readonly=True, default=generate_UUID())


    # Sets the invoice's providerID as Taler
    provider_id = fields.Many2one(
        "payment.provider",
        string="Taler Provider",
        default=lambda self: self.env["payment.provider"].search([("code", "=", "taler")], limit=1).id,
    )

    def getToken(self):
        requestGetToken(self)

    def action_post(self):
        res = super().action_post()

        for move in self:
            if move.move_type in ('out_invoice') and move.preferred_payment_method_line_id.code == "taler":  # Only invoices/bills, and only those to be paid with Taler
                self.is_taler_invoice = True
                move._taler_invoice_create()
        return res

    def _taler_invoice_create(self):
        order_summary = "Odoo reference " + self.name + " for " + str(self.amount_total) + str(self.currency_id.symbol) + " " + self.currency_id.name
        currency = self.currency_id.name # Gets the currency by name for the current order
        if self.provider_id.is_in_test_mode(): # Checks if provider used is currently in test mode, and if so, uses KUDOS as currency (Kudos is the Taler test currency)
            currency = "KUDOS"
        self.getToken()
        invoice_due_date_in_epoch = get_datetime_date_to_epoch(self.invoice_date_due) # Calculate the invoice due date in epoch seconds, to be used in the Taler order creation to set a max payment date
        self.taler_order_id, self.taler_order_url, self.taler_order_uri = postPlaceOrderWithFulfillmentMessage(self,
                                                                                                               currency,
                                                                                                               self.amount_total,
                                                                                                               order_summary,
                                                                                                               self.provider_id.fulfillment_message + " Reference: " + self.taler_uuid,
                                                                                                               invoice_due_date_in_epoch) #Uses the invoice due date as expiration date of the payment
        self.taler_qr = generate_qr(self.taler_order_uri)
