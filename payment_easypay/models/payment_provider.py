# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
import pprint

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from .. import const
from .. import utils as easypay_utils

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("easypay", "EasyPay")], ondelete={"easypay": "set default"}
    )
    easypay_account_id = fields.Char(
        string="Account ID",
        help="The Account ID provided by EasyPay",
    )
    easypay_api_key = fields.Char(
        string="API Key",
        help="The API Key provided by EasyPay",
        groups="base.group_system",
    )
    easypay_payment_method = fields.Selection(
        selection=[("cc", "Credit/Debit Card")],
        string="Payment Method",
        default="cc",
        required_if_provider="easypay",
        help="The payment method to use with EasyPay",
    )
    easypay_use_checkout = fields.Boolean(
        string="Use Checkout",
        default=False,
        help="Use EasyPay Checkout for a better user experience",
    )

    # === COMPUTE METHODS ===#

    def _compute_feature_support_fields(self):
        """Override of `payment` to enable additional features."""
        res = super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == "easypay").update(
            {
                "support_manual_capture": "full_only",
                "support_refund": "partial",
            }
        )
        return res

    def _easypay_get_inline_form_values(self, amount, currency, partner_id, tx_sudo):
        """Return the inline form values for EasyPay Checkout.

        Note: self.ensure_one()

        :param float amount: The transaction amount
        :param res.currency currency: The transaction currency
        :param res.partner partner_id: The transaction partner
        :param payment.transaction tx_sudo: The sudoed transaction
        :return: The inline form values
        :rtype: str (JSON)
        """
        self.ensure_one()

        if self.easypay_use_checkout:
            response = self._easypay_create_checkout_session(tx_sudo)
            tx_sudo.easypay_checkout_id = response.get("id")

            import json

            return json.dumps(
                {
                    "checkout_manifest": response.get("session"),
                    "checkout_id": response.get("id"),
                    "api_url": self._easypay_get_api_url(),
                }
            )

        return json.dumps({})

    # === BUSINESS METHODS - GETTERS ===#

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "easypay":
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _easypay_get_api_url(self):
        """Return the API URL based on the provider state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        if self.state == "enabled":
            return const.API_URL_PROD
        return const.API_URL_TEST

    # === BUSINESS METHODS - PAYMENT FLOW ===#

    def _easypay_make_request(self, endpoint, payload=None, method="POST"):
        """Make a request to the EasyPay API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The API endpoint (e.g., '/2.0/single')
        :param dict payload: The payload of the request
        :param str method: The HTTP method of the request
        :return: The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()

        url = f"{self._easypay_get_api_url()}{endpoint}"
        headers = {
            "AccountId": easypay_utils.get_account_id(self),
            "ApiKey": easypay_utils.get_api_key(self),
            "Content-Type": "application/json",
        }

        _logger.debug(
            "API request to %s with payload:\n%s", url, pprint.pformat(payload)
        )

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=60)
            elif method == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=60)
            elif method == "PATCH":
                response = requests.patch(
                    url, json=payload, headers=headers, timeout=60
                )
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=60)
            else:
                raise ValidationError(_("Unsupported HTTP method: %s") % method)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as err:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError(
                _("EasyPay: Could not establish the connection to the API.")
            ) from err
        except requests.exceptions.HTTPError as err:
            _logger.exception("invalid API request at %s with data %s", url, payload)
            error_msg = ""
            try:
                error_msg = response.json().get("message", "")
            except Exception:  # pragma: no cover - fallback when no JSON
                try:
                    error_msg = response.text[:500]
                except Exception:  # pragma: no cover - last resort
                    error_msg = ""
            raise ValidationError(
                _(
                    "EasyPay: The communication with the API failed.\n"
                    "EasyPay gave us the following info about the problem:\n"
                    "'%s'"
                )
                % error_msg
            ) from err

    def _easypay_create_checkout_session(self, tx_sudo):
        """Create a checkout session with EasyPay.

        Note: self.ensure_one()

        :param payment.transaction tx_sudo: The sudoed transaction of the payment.
        :return: The checkout session data
        :rtype: dict
        """
        self.ensure_one()

        # EasyPay supports EUR. Prevent invalid currency requests early.
        if tx_sudo.currency_id.name != "EUR":
            raise ValidationError(
                _("EasyPay: Only EUR currency is supported for checkout.")
            )

        payload = {
            "type": ["single"],
            "payment": {
                "methods": [self.easypay_payment_method],
                "type": const.PAYMENT_TYPE_SALE,
                "capture": {
                    "descriptive": tx_sudo.reference,
                    "transaction_key": tx_sudo.reference,
                },
                "currency": tx_sudo.currency_id.name,
                "key": tx_sudo.reference,
            },
            "order": {
                "key": tx_sudo.reference,
                "value": tx_sudo.amount,
            },
            "customer": easypay_utils.include_customer_data(tx_sudo),
        }
        return self._easypay_make_request("/2.0/checkout", payload)

    def _easypay_create_single_payment(self, tx_sudo):
        """Create a single payment with EasyPay.

        Note: self.ensure_one()

        :param payment.transaction tx_sudo: The sudoed transaction of the payment.
        :return: The payment data
        :rtype: dict
        """
        self.ensure_one()

        # EasyPay supports EUR. Prevent invalid currency requests early.
        if tx_sudo.currency_id.name != "EUR":
            raise ValidationError(
                _("EasyPay: Only EUR currency is supported for payments.")
            )

        base_url = tx_sudo.provider_id.get_base_url()
        return_url = f"{base_url}/payment/easypay/return"
        _logger.debug("Single payment return URL: %s", return_url)
        payload = {
            "type": const.PAYMENT_TYPE_SALE,
            "method": self.easypay_payment_method,
            "value": tx_sudo.amount,
            "currency": tx_sudo.currency_id.name,
            "key": tx_sudo.reference,
            "capture": {
                "descriptive": tx_sudo.reference,
                "transaction_key": tx_sudo.reference,
            },
            "customer": easypay_utils.include_customer_data(tx_sudo),
            "return_url": return_url,
        }
        return self._easypay_make_request("/2.0/single", payload)
