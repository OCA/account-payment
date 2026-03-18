# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from odoo.exceptions import ValidationError
from odoo import models, fields
from odoo.addons.payment_taler.utils.utils import talog, tawarn, tadebug, taerror, generate_UUID, get_datetime_now_to_epoch, generate_qr
from odoo.addons.payment_taler.models.taler_api_methods import requestGetToken, postPlaceOrderWithFulfillmentUrl, getOrderTalerUri, requestGetOrderFromId, getOrderIdStatus, checkOrderIsPaid, requestRefundForOrder
from odoo.addons.payment_taler.controllers.taler_controller import TalerController
from odoo.tools import _

class TalerTransaction(models.Model):
    _inherit = 'payment.transaction'
    #Because this model inherits, and does not have its own name, there is no need for it to appear in ir.model.access.csv
    #It will inherit the ir security settings from the account.move model

    taler_order_id = fields.Char(string="Taler order ID", default="")
    taler_order_url = fields.Char(string="Taler order URL", default="")
    taler_order_uri = fields.Char(string="Taler order URI", default="")

    # This UUID is only used for the fulfillment url. Without the UUID in the url, the Taler merchant could mix up two orders with the same Odoo ID, on two different Odoo instances
    # This is not a perfect solution, as two duplicate UUID + OrderID could be generated on two different Odoo instances, on the same Taler Merchant, but this is highly unlikely.
    taler_uuid = fields.Char(string="Taler UUID", readonly=True, default=generate_UUID())

    # These fields are only used for refund transaction
    taler_refund_qr = fields.Char(string="Taler Refund QR Code", default="")
    taler_refund_uri = fields.Char(string="Taler Refund URI", default="")

    def getToken(self):
        requestGetToken(self)

    def isPaid(self):
        return checkOrderIsPaid(self)

    def getCurrency(self):
        if self.provider_code == 'taler' and self.provider_id.is_in_test_mode():  # Checks if the payment provider is currently in test mode
            return "KUDOS"
        return self.currency_id.name

    def _process_notification_data(self, data):
        super()._process_notification_data(data)
        if self.provider_code != 'taler':
            tadebug("Getting different provider code than taler: ", self.provider_code, ". This is not necessarily an error")
            return
        self.provider_reference = data.get('merchantOrderId')

        # Update the payment state based on payment status on the merchant's side
        payment_status = data.get('paymentStatus')
        if (payment_status == 'paid'):
            talog("Order paid: ", self.reference)
            self._set_done()
        elif (payment_status == 'claimed'):
            talog("Order is claimed by a wallet")
        elif (payment_status == 'unpaid'):
            talog("Order is unpaid")
        else:
            tawarn("Received data with invalid payment status " + payment_status + " for transaction with reference " + self.reference + " and taler order id " + data.get('merchantOrderId'))
            tawarn("Setting this transaction as cancelled, with error")
            self._set_canceled()
            self._set_error("Taler: Received data with invalid payment status: " + payment_status)


    def _get_specific_rendering_values(self, values):
        """ Overrides the rendering values method to insert the Taler flow """
        new_values = super()._get_specific_rendering_values(values)
        if self.provider_code != 'taler':
            return new_values
        order_summary = "Odoo reference " + self.reference + " for " + str(self.amount) + str(self.currency_id.symbol) + " " + self.currency_id.name
        currency = self.getCurrency()
        self.getToken()
        expiration_time_in_epoch = get_datetime_now_to_epoch(15)  # Calculate the epoch seconds in 15 minutes, to be used in the Taler order creation to set a max payment date
        self.taler_order_id, self.taler_order_url, self.taler_order_uri = postPlaceOrderWithFulfillmentUrl(
                                                                                  self,
                                                                                  currency,
                                                                                  self.amount,
                                                                                  order_summary,
                                                                                  self.provider_id.fulfillment_message,
                                                                                  TalerController._fulfillment_url + "/" + self.taler_uuid,
                                                                                  expiration_time_in_epoch)  # Orders expire 15 minutes after creation
        rendering_values = {
            'taler_merchant_url': self.taler_order_url
        }
        tadebug("Order Taler Id: ", self.taler_order_id)
        tadebug("Order Reference: ", self.reference)

        return rendering_values

    def _get_orderid_status(self):
        return getOrderIdStatus(self)

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on taler data."""
        transaction = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'taler' or len(transaction) == 1:
            return transaction

        reference = notification_data.get('reference')
        if not reference:
            taerror("Taler: Received data with missing reference.")
            taerror(notification_data)
            raise ValidationError(_("Taler: Received data with missing reference."))
        transaction = self.search([('reference', '=', reference), ('provider_code', '=', 'taler')])

        if not transaction:
            raise ValidationError(_("Taler: No transaction found matching reference " + reference))

        return transaction


    def _send_refund_request(self, amount_to_refund=None):
        """ Override of the refund request process to integrate the Taler refund flow """
        # The refund_txn object is returned from super(), but it actually has the same fields as those implemented
        # in this TalerTransaction class, so that includes the taler_refund_uri and taler_refund_qr fields
        refund_txn = super()._send_refund_request(amount_to_refund=amount_to_refund)

        if self.provider_code != 'taler':
            return refund_txn

        amount = amount_to_refund or self.amount
        currency = self.getCurrency()

        reason = "Refunding the product"
        response = ""
        self.getToken()

        try:
            tadebug("Sending refund request to the Taler merchant")
            taler_refund_uri = requestRefundForOrder(self, amount, currency, reason)
        except Exception as e:
            taerror("Error in refund response from Taler merchant. Response received from Taler merchant: ")
            taerror(response)
            raise ValidationError(_("Error in refund response from Taler, see logs"))

        taler_refund_qr = generate_qr(taler_refund_uri)

        refund_txn.taler_refund_uri = taler_refund_uri
        refund_txn.taler_refund_qr = taler_refund_qr

        # The reference and taler_refund_uri would have these value only if we were unit testing, and in unit testing we don't want to test the email sending
        if self.reference != "Test Transaction" and refund_txn.taler_refund_uri != "taler://mock_refund_uri/":
            self._send_refund_email(refund_txn)

        refund_txn._set_done()
        return refund_txn

    def _send_refund_email(self, refund_txn):
        """ Send an email to the customer containing the refund QR Code """
        email_refund_template_name = "payment_taler.email_refund"
        template = self.env.ref(email_refund_template_name)
        if template:
            # Send email
            template.send_mail(refund_txn.id, force_send=True)
        else:
            raise ValidationError(_("Email template not found! Looking for: " + email_refund_template_name))
