# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import pprint

from lxml import etree, objectify
from werkzeug import urls

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_ogone.controllers.main import OgoneController

from . import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator="-", **kwargs):
        """Override of payment to ensure that Ogone requirements for references are satisfied.

        Ogone requirements for references are as follows:
        - References must be unique at provider level for a given merchant account.
          This is satisfied by singularizing the prefix with the current datetime.
          If two transactions are created simultaneously, `_compute_reference` ensures
          the uniqueness of references by suffixing a sequence number.

        :param str provider_code: The code of the provider handling the transaction
        :param str prefix: The custom prefix used to compute the full reference
        :param str separator: The custom separator used to separate the prefix from the suffix
        :return: The unique reference for the transaction
        :rtype: str
        """
        if provider_code != "ogone":
            return super()._compute_reference(provider_code, prefix=prefix, **kwargs)

        if not prefix:
            # If no prefix is provided, it could mean that a module has passed a kwarg
            # intended for the `_compute_reference_prefix` method, as it is only called
            # if the prefix is empty.
            # We call it manually here because singularizing the prefix would generate a default
            # value if it was empty, hence preventing the method from ever being called and the
            # transaction from received a reference named after the related document.
            prefix = (
                self.sudo()._compute_reference_prefix(
                    provider_code, separator, **kwargs
                )
                or None
            )
        prefix = payment_utils.singularize_reference_prefix(
            prefix=prefix, max_length=40
        )
        reference = super()._compute_reference(provider_code, prefix=prefix, **kwargs)
        if self._context.get("refund_move_id", False):
            refund_move = self.env["account.move"].browse(
                self._context.get("refund_move_id")
            )
            reference = refund_move.name
        return reference

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return Ogone-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values
                                       of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "ogone":
            return res

        return_url = urls.url_join(
            self.provider_id.get_base_url(), OgoneController._return_url
        )
        rendering_values = {
            "PSPID": self.provider_id.ogone_pspid,
            "ORDERID": self.reference,
            "AMOUNT": payment_utils.to_minor_currency_units(self.amount, None, 2),
            "CURRENCY": self.currency_id.name,
            "LANGUAGE": self.partner_lang or "en_US",
            "EMAIL": self.partner_email or "",
            "OWNERADDRESS": self.partner_address or "",
            "OWNERZIP": self.partner_zip or "",
            "OWNERTOWN": self.partner_city or "",
            "OWNERCTY": self.partner_country_id.code or "",
            "OWNERTELNO": self.partner_phone or "",
            "OPERATION": "SAL",  # direct sale
            "USERID": self.provider_id.ogone_userid,
            "ACCEPTURL": return_url,
            "DECLINEURL": return_url,
            "EXCEPTIONURL": return_url,
            "CANCELURL": return_url,
        }
        if self.tokenize:
            rendering_values.update(
                {
                    "ALIAS": payment_utils.singularize_reference_prefix(
                        prefix="ODOO-ALIAS"
                    ),
                    "ALIASUSAGE": _(
                        "Storing your payment details is necessary for future use."
                    ),
                }
            )
        rendering_values.update(
            {
                "SHASIGN": self.provider_id._ogone_generate_signature(
                    rendering_values, incoming=False
                ).upper(),
                "api_url": self.provider_id._ogone_get_api_url("hosted_payment_page"),
            }
        )
        return rendering_values

    def _get_payment_request_data(self):
        if self.env.context.get(
            "active_model"
        ) == "account.move" and self.env.context.get("active_id"):
            invoice = self.env["account.move"].browse(self.env.context.get("active_id"))
        data = {
            # DirectLink parameters
            "PSPID": self.provider_id.ogone_pspid,
            "ORDERID": self.reference,
            "INVORDERID": invoice.name or "",
            "INVDATE": invoice.invoice_date.strftime("%m/%d/%Y") or "",
            "USERID": self.provider_id.ogone_userid,
            "PSWD": self.provider_id.ogone_password,
            "AMOUNT": payment_utils.to_minor_currency_units(self.amount, None, 2),
            "CURRENCY": self.currency_id.name,
            "CN": self.partner_name or "",  # Cardholder Name
            "EMAIL": self.partner_email or "",
            "OWNERADDRESS": self.partner_address or "",
            "OWNERZIP": self.partner_zip or "",
            "OWNERTOWN": self.partner_city or "",
            "OWNERCTY": self.partner_country_id.code or "",
            "OWNERTELNO": self.partner_phone or "",
            "OPERATION": "SAL",  # direct sale
            # Alias Manager parameters
            "ALIAS": self.token_id.provider_ref,
            "ALIASPERSISTEDAFTERUSE": "Y",
            "ECI": 9,  # Recurring (from eCommerce)
        }
        return self._get_item_request_data(data, invoice)

    def _send_payment_request(self):
        """Override of payment to send a payment request to Ogone.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        if self.provider_code != "ogone":
            return

        if not self.token_id:
            raise UserError(_("Ogone: The transaction is not linked to a token."))

        # Make the payment request
        data = self._get_payment_request_data()
        data["SHASIGN"] = self.provider_id._ogone_generate_signature(
            data, incoming=False
        )

        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat({k: v for k, v in data.items() if k != "PSWD"}),
        )  # Log the payment request data without the password
        response_content = self.provider_id._ogone_make_request(data)
        try:
            tree = objectify.fromstring(response_content)
        except etree.XMLSyntaxError as e:
            raise ValidationError(
                _("Ogone: Received badly structured response from the API.")
            ) from e

        # Handle the feedback data
        _logger.info(
            "payment request response (as an etree) for transaction with reference %s:\n%s",
            self.reference,
            etree.tostring(tree, pretty_print=True, encoding="utf-8"),
        )
        feedback_data = {"ORDERID": tree.get("orderID"), "tree": tree}
        _logger.info(
            "handling feedback data from Ogone for transaction with reference %s with"
            " data:\n%s",
            self.reference,
            pprint.pformat(feedback_data),
        )
        self._handle_notification_data("ogone", feedback_data)

    def _get_refund_request_data(self, invoice, refund_move):
        data = {
            # DirectLink parameters
            "PSPID": self.provider_id.ogone_pspid,
            "PAYID": self.provider_reference,
            "INVORDERID": refund_move.name,
            "USERID": self.provider_id.ogone_userid,
            "PSWD": self.provider_id.ogone_password,
            "AMOUNT": payment_utils.to_minor_currency_units(self.amount, None, 2),
            "CURRENCY": self.currency_id.name,
            "CN": self.partner_name or "",  # Cardholder Name
            "OPERATION": "RFD",  # refund
            "OR_INVORDERID": invoice.name or "",
            "AMOUNTHTVA": payment_utils.to_minor_currency_units(
                invoice.amount_untaxed, None, 2
            ),
            "AMOUNTTVA": payment_utils.to_minor_currency_units(
                invoice.amount_tax, None, 2
            ),
            "DATATYPE": "LID",
            # Alias Manager parameters
            "ALIAS": self.token_id.provider_ref,
            "ALIASPERSISTEDAFTERUSE": "Y",
        }
        return self._get_item_request_data(data, invoice)

    def _send_refund_request(self, amount_to_refund=None):
        """Override of payment to send a refund request to Ogone.

        Note: self.ensure_one()

        :param float amount_to_refund: The amount to refund.
        :return: The refund transaction created to process the refund request.
        :rtype: recordset of `payment.transaction`
        """
        if self.payment_id.state != "posted":
            raise ValidationError(_("Only accounted payment can be refunded."))

        invoice = self.payment_id.reconciled_invoice_ids[0]
        default_values_list = [
            {
                "ref": _("Reversal of: %s", invoice.name),
                "invoice_origin": invoice.name,
            }
        ]
        refund_move = invoice._reverse_moves(
            default_values_list=default_values_list, cancel=False
        )
        refund_move.action_post()
        self = self.with_context(refund_move_id=refund_move.id)
        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        if (
            self.provider_code != "ogone"
            or len(self.payment_id.reconciled_invoice_ids) != 1
        ):
            return refund_tx

        if not self.token_id:
            raise UserError(_("Ogone: The transaction is not linked to a token."))

        # Make the refund request to ogone.
        invoice = self.payment_id.reconciled_invoice_ids[0]
        data = self._get_refund_request_data(invoice=invoice, refund_move=refund_move)
        data["SHASIGN"] = self.provider_id._ogone_generate_signature(
            data, incoming=False
        )

        _logger.info(
            "refund request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat({k: v for k, v in data.items() if k != "PSWD"}),
        )  # Log the refund request data without the password
        response_content = self.provider_id._ogone_make_request(data)
        try:
            tree = objectify.fromstring(response_content)
        except etree.XMLSyntaxError as e:
            raise ValidationError(
                _("Ogone: Received badly structured response from the API.")
            ) from e

        # Handle the feedback data
        _logger.info(
            "refund request response (as an etree) for transaction with reference %s:\n%s",
            self.reference,
            etree.tostring(tree, pretty_print=True, encoding="utf-8"),
        )
        feedback_data = {"ORDERID": tree.get("orderID"), "tree": tree}
        _logger.info(
            "handling feedback data from Ogone for transaction with reference %s with"
            " data:\n%s",
            self.reference,
            pprint.pformat(feedback_data),
        )
        refund_tx._handle_notification_data("ogone", feedback_data)

        return refund_tx

    def _get_item_request_data(self, data, invoice):
        idx = 1
        for line in invoice.invoice_line_ids.filtered(lambda line: line.product_id):
            if line.tax_ids:
                vat_code = str(line.tax_ids[0].amount) + "%"
            else:
                vat_code = "0.0%"
            data.update(
                {
                    "ITEMID" + str(idx): str(line.id),
                    "ITEMNAME" + str(idx): line.name[:40],
                    "ITEMPRICE"
                    + str(idx): payment_utils.to_minor_currency_units(
                        line.price_unit, None, 2
                    ),
                    "TAXINCLUDED" + str(idx): str(0),
                    "ITEMVATCODE" + str(idx): vat_code,
                    "ITEMQUANT" + str(idx): line.quantity,
                    "LIDEXCL"
                    + str(idx): payment_utils.to_minor_currency_units(
                        line.price_subtotal, None, 2
                    ),
                }
            )
            idx += 1
        return data

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on Ogone data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(
            provider_code=provider_code, notification_data=notification_data
        )
        if provider_code != "ogone" or len(tx) == 1:
            return tx

        reference = notification_data.get("ORDERID")
        tx = self.search(
            [("reference", "=", reference), ("provider_code", "=", "ogone")]
        )

        # Refund transaction to update status
        if tx and notification_data.get("STATUS") == "8":
            tx = tx.child_transaction_ids.filtered(
                lambda t: t.state == "pending" and t.operation == "refund"
            )

        if not tx:
            raise ValidationError(
                _("Ogone: No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on Ogone data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "ogone":
            return

        if "tree" in notification_data:
            notification_data = notification_data["tree"]

        self.provider_reference = notification_data.get("PAYID")
        payment_status = int(notification_data.get("STATUS", "0"))
        if payment_status in const.PAYMENT_STATUS_MAPPING["pending"]:
            self._set_pending()
        elif payment_status in const.PAYMENT_STATUS_MAPPING["authorized"]:
            self._set_authorized()
        elif payment_status in const.PAYMENT_STATUS_MAPPING["done"]:
            has_token_data = "ALIAS" in notification_data
            if self.tokenize and has_token_data:
                self._ogone_tokenize_from_notification_data(notification_data)
            self._set_done()
            # Immediately post-process the transaction if it is a refund
            if self.operation == "refund":
                self.env.ref("payment.cron_post_process_payment_tx")._trigger()
        elif payment_status in const.PAYMENT_STATUS_MAPPING["cancel"]:
            self._set_canceled()
        elif payment_status in const.PAYMENT_STATUS_MAPPING["declined"]:
            if notification_data.get("NCERRORPLUS"):
                reason = notification_data.get("NCERRORPLUS")
            elif notification_data.get("NCERROR"):
                reason = "Error code: %s" % notification_data.get("NCERROR")
            else:
                reason = "Unknown reason"
            _logger.info("the payment has been declined: %s.", reason)
            self._set_error("Ogone: " + _("The payment has been declined: %s", reason))
        else:  # Classify unknown payment statuses as `error` tx state
            _logger.info(
                "received data with invalid payment status (%s) for transaction with"
                " reference %s",
                payment_status,
                self.reference,
            )
            self._set_error(
                "Ogone: "
                + _("Received data with invalid payment status: %s", payment_status)
            )

    def _ogone_tokenize_from_notification_data(self, notification_data):
        """Create a token from notification data.

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        token = self.env["payment.token"].create(
            {
                "provider_id": self.provider_id.id,
                "payment_details": notification_data.get("CARDNO")[
                    -4:
                ],  # Ogone pads details with X's.
                "partner_id": self.partner_id.id,
                "provider_ref": notification_data["ALIAS"],
                "verified": True,  # The payment is authorized, so the payment method is valid
            }
        )
        self.write(
            {
                "token_id": token.id,
                "tokenize": False,
            }
        )
        _logger.info(
            "created token with id %(token_id)s for partner with id %(partner_id)s from "
            "transaction with reference %(ref)s",
            {
                "token_id": token.id,
                "partner_id": self.partner_id.id,
                "ref": self.reference,
            },
        )

    def _create_payment(self, **extra_create_values):
        payment = super()._create_payment(**extra_create_values)
        if self.provider_code == "ogone" and self.amount < 0:
            payment_method_line = (
                self.provider_id.journal_id.outbound_payment_method_line_ids.filtered(
                    lambda l: l.code == self.provider_code
                )
            )
            if payment_method_line:
                payment.payment_method_line_id = payment_method_line.id
            # reconcile reverse move with refund payment
            invoice = payment.source_payment_id.reconciled_invoice_ids[0]
            refund_move = invoice.reversal_move_id[0]
            refund_move.write(
                {
                    "payment_reference": payment.ref,
                }
            )
            (payment.line_ids + refund_move.line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                and not line.reconciled
            ).reconcile()
        return payment
