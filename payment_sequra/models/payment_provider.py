# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import logging

import requests

from odoo import fields, models
from odoo.exceptions import UserError

from .. import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("sequra", "SeQura")], ondelete={"sequra": "set default"}
    )
    sequra_merchant_id = fields.Char(
        required_if_provider="sequra", groups="base.group_system"
    )
    sequra_account_key = fields.Char(
        required_if_provider="sequra", groups="base.group_system"
    )
    sequra_account_secret = fields.Char(
        required_if_provider="sequra", groups="base.group_system"
    )

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "sequra":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _sequra_get_base_url(self):
        self.ensure_one()
        return (
            "https://sandbox.sequrapi.com"
            if self.state == "test"
            else "https://live.sequrapi.com"
        )

    def _sequra_make_request(self, endpoint, payload=None, method="POST"):
        self.ensure_one()
        base_url = self._sequra_get_base_url()
        url = endpoint if endpoint.startswith("http") else f"{base_url}{endpoint}"
        credentials = f"{self.sequra_account_key}:{self.sequra_account_secret}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
            "utf-8"
        )
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Sequra-Merchant-Id": self.sequra_merchant_id,
            "Authorization": f"Basic {encoded_credentials}",
        }
        try:
            response = requests.request(
                method, url, json=payload, headers=headers, timeout=20
            )
        except requests.RequestException as e:
            _logger.exception("Connection error contacting SeQura API: %s", e)
            raise UserError(self.env._("Could not reach SeQura API: %s") % e) from e
        if response.status_code not in (200, 202, 204, 409):
            _logger.error(
                "SeQura API error [%s]: %s", response.status_code, response.text
            )
            raise UserError(
                self.env._("SeQura API request failed (%s): %s")
                % (response.status_code, response.text)
            )
        return response

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "sequra":
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES
