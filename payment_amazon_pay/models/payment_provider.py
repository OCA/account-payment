import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from werkzeug.urls import url_join

from odoo import fields, models
from odoo.exceptions import ValidationError


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("amazon_pay", "Amazon Pay")],
        ondelete={"amazon_pay": "set default"},
    )

    amazon_pay_merchant_id = fields.Char(
        string="Merchant ID",
        required_if_provider="amazon_pay",
        help="Amazon Pay merchant identifier.",
    )
    amazon_pay_store_id = fields.Char(
        string="Store ID",
        required_if_provider="amazon_pay",
        help="Amazon Pay Checkout v2 store identifier.",
    )
    amazon_pay_public_key_id = fields.Char(
        string="Public Key ID",
        required_if_provider="amazon_pay",
        help="Amazon Pay public key ID used to sign requests.",
    )
    amazon_pay_private_key = fields.Char(
        string="Private Key",
        required_if_provider="amazon_pay",
        groups="base.group_system",
        help="Amazon Pay Checkout v2 private key in PEM format.",
    )
    amazon_pay_region = fields.Selection(
        selection=[("eu", "Europe"), ("na", "North America"), ("jp", "Japan")],
        string="Region",
        default="eu",
        required=True,
    )
    amazon_pay_checkout_language = fields.Selection(
        selection=[
            ("es_ES", "Spanish"),
            ("en_GB", "English (UK)"),
            ("de_DE", "German"),
            ("fr_FR", "French"),
            ("it_IT", "Italian"),
            ("en_US", "English (US)"),
            ("ja_JP", "Japanese"),
        ],
        string="Checkout Language",
        default="es_ES",
        required=True,
    )
    amazon_pay_soft_descriptor = fields.Char(
        string="Soft Descriptor",
        help="Optional text displayed on the buyer statement when supported.",
    )
    amazon_pay_sandbox_simulation_code = fields.Char(
        string="Sandbox Simulation Code",
        help="Optional sandbox simulation code used by Amazon Pay.",
    )

    def _compute_feature_support_fields(self):
        """Override of `payment` to enable additional features."""
        res = super()._compute_feature_support_fields()
        amazon_providers = self.filtered(lambda provider: provider.code == "amazon_pay")
        amazon_providers.update(
            {
                "support_express_checkout": False,
                "support_manual_capture": False,
                "support_refund": "partial",
                "support_tokenization": False,
            }
        )
        return res

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "amazon_pay":
            return default_codes
        return {*default_codes, "amazon_pay"}

    def _get_redirect_form_view(self, is_validation=False):
        self.ensure_one()
        if self.code != "amazon_pay":
            return super()._get_redirect_form_view(is_validation=is_validation)
        return self.env.ref("payment_amazon_pay.amazon_pay_redirect_form")

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.code != "amazon_pay":
            return super()._get_supported_currencies()
        supported_currency_codes = {
            "eu": ["EUR", "GBP"],
            "na": ["USD"],
            "jp": ["JPY"],
        }[self.amazon_pay_region]
        return (
            self.env["res.currency"]
            .with_context(active_test=False)
            .search([("name", "in", supported_currency_codes)])
        )

    def _amazon_pay_get_host(self):
        self.ensure_one()
        return {
            "eu": "pay-api.amazon.eu",
            "na": "pay-api.amazon.com",
            "jp": "pay-api.amazon.jp",
        }[self.amazon_pay_region]

    def _amazon_pay_get_environment(self):
        self.ensure_one()
        return "sandbox" if self.state == "test" else "live"

    def _amazon_pay_get_api_path(self, endpoint):
        self.ensure_one()
        return f"/{self._amazon_pay_get_environment()}/v2/{endpoint.lstrip('/')}"

    def _amazon_pay_get_api_url(self, endpoint):
        self.ensure_one()
        return f"https://{self._amazon_pay_get_host()}{self._amazon_pay_get_api_path(endpoint)}"

    def _amazon_pay_get_region_code(self):
        self.ensure_one()
        return self.amazon_pay_region

    @staticmethod
    def _amazon_pay_format_amount(amount):
        return f"{amount:.2f}"

    @staticmethod
    def _amazon_pay_normalize_private_key(key):
        """Reconstruct PEM format if newlines were stripped."""
        import re

        key = key.strip()
        if "\n" not in key and "-----" in key:
            match = re.match(r"(-----BEGIN[^-]+-----)([^-]+)(-----END[^-]+-----)", key)
            if match:
                header, data, footer = match.groups()
                data = data.replace(" ", "")
                data = "\n".join(data[i : i + 64] for i in range(0, len(data), 64))
                key = f"{header}\n{data}\n{footer}"
        return key

    def _amazon_pay_build_headers(
        self, method, api_path, payload_text="", idempotency_key=None
    ):
        self.ensure_one()
        if not self.amazon_pay_private_key:
            raise ValidationError(self.env._("Amazon Pay private key is missing."))

        amz_date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        payload_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
        headers_to_sign = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-amz-pay-date": amz_date,
            "x-amz-pay-host": self._amazon_pay_get_host(),
            "x-amz-pay-region": self._amazon_pay_get_region_code(),
        }
        if idempotency_key:
            headers_to_sign["x-amz-pay-idempotency-key"] = idempotency_key
        if self.state == "test" and self.amazon_pay_sandbox_simulation_code:
            headers_to_sign["x-amz-simulation-code"] = (
                self.amazon_pay_sandbox_simulation_code
            )

        signed_header_names = sorted(headers_to_sign)
        canonical_headers = "".join(
            f"{name}:{headers_to_sign[name]}\n" for name in signed_header_names
        )
        signed_headers = ";".join(signed_header_names)
        canonical_request = (
            f"{method.upper()}\n"
            f"{api_path}\n"
            f"\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )
        string_to_sign = (
            "AMZN-PAY-RSASSA-PSS-V2\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        private_key = serialization.load_pem_private_key(
            self._amazon_pay_normalize_private_key(self.amazon_pay_private_key).encode(
                "utf-8"
            ),
            password=None,
        )
        signature = private_key.sign(
            string_to_sign.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        authorization = (
            "AMZN-PAY-RSASSA-PSS-V2 "
            f"PublicKeyId={self.amazon_pay_public_key_id}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={base64.b64encode(signature).decode('ascii')}"
        )

        headers = dict(headers_to_sign)
        headers["authorization"] = authorization
        return headers

    def _amazon_pay_request(self, method, endpoint, payload=None, idempotency_key=None):
        self.ensure_one()
        payload = payload or {}
        payload_text = (
            ""
            if method.upper() == "GET"
            else json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        )
        api_path = self._amazon_pay_get_api_path(endpoint)
        headers = self._amazon_pay_build_headers(
            method, api_path, payload_text=payload_text, idempotency_key=idempotency_key
        )
        response = requests.request(
            method=method.upper(),
            url=self._amazon_pay_get_api_url(endpoint),
            data=payload_text or None,
            headers=headers,
            timeout=60,
        )
        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {"message": response.text}
        if response.status_code >= 400:
            message = (
                data.get("reasonDescription") or data.get("message") or response.text
            )
            raise ValidationError(self.env._("Amazon Pay API error: %s") % message)
        data["_http_status"] = response.status_code
        return data

    def _amazon_pay_prepare_checkout_payload(self, tx):
        self.ensure_one()
        tx.ensure_one()
        base_url = self.get_base_url()
        result_url = url_join(
            base_url, f"/payment/amazon_pay/return?reference={tx.reference}"
        )
        cancel_url = url_join(
            base_url, f"/payment/amazon_pay/cancel?reference={tx.reference}"
        )
        payload = {
            "storeId": self.amazon_pay_store_id,
            "webCheckoutDetails": {
                "checkoutMode": "ProcessOrder",
                "checkoutResultReturnUrl": result_url,
                "checkoutCancelUrl": cancel_url,
            },
            "paymentDetails": {
                "paymentIntent": "AuthorizeWithCapture",
                "chargeAmount": {
                    "amount": self._amazon_pay_format_amount(tx.amount),
                    "currencyCode": tx.currency_id.name,
                },
            },
            "chargePermissionType": "OneTime",
            "merchantMetadata": {
                "merchantReferenceId": tx.reference,
                "merchantStoreName": (self.company_id.name or self.name or "Store")[
                    :50
                ],
                "customInformation": tx.reference,
            },
            "productType": "PayOnly",
            "scopes": ["name", "email", "phoneNumber", "billingAddress"],
        }
        if self.amazon_pay_soft_descriptor:
            payload["paymentDetails"]["softDescriptor"] = (
                self.amazon_pay_soft_descriptor[:16]
            )
        return payload

    def _amazon_pay_get_button_payload(self, tx):
        """Return config dict for the Amazon Pay Button JS widget.

        Uses AMZN-PAY-RSASSA-PSS (salt=20) as required by the button SDK,
        distinct from the API request signing (V2, salt=32).
        """
        self.ensure_one()
        tx.ensure_one()
        payload = self._amazon_pay_prepare_checkout_payload(tx)
        payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        string_to_sign = f"AMZN-PAY-RSASSA-PSS\n{payload_hash}"
        private_key = serialization.load_pem_private_key(
            self._amazon_pay_normalize_private_key(self.amazon_pay_private_key).encode(
                "utf-8"
            ),
            password=None,
        )
        signature = private_key.sign(
            string_to_sign.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=20),
            hashes.SHA256(),
        )
        checkout_js_url = {
            "eu": "https://static-eu.payments-amazon.com/checkout.js",
            "na": "https://static-na.payments-amazon.com/checkout.js",
            "jp": "https://static-fe.payments-amazon.com/checkout.js",
        }[self.amazon_pay_region]
        return {
            "checkout_js_url": checkout_js_url,
            "merchant_id": self.amazon_pay_merchant_id,
            "public_key_id": self.amazon_pay_public_key_id,
            "ledger_currency": tx.currency_id.name,
            "checkout_language": self.amazon_pay_checkout_language or "en_US",
            "sandbox": self.state == "test",
            "payload_json": payload_json,
            "signature": base64.b64encode(signature).decode(),
        }

    def _amazon_pay_create_checkout_session(self, tx):
        self.ensure_one()
        return self._amazon_pay_request(
            "POST",
            "checkoutSessions",
            payload=self._amazon_pay_prepare_checkout_payload(tx),
            idempotency_key=uuid.uuid4().hex,
        )

    def _amazon_pay_complete_checkout_session(self, tx, checkout_session_id):
        self.ensure_one()
        tx.ensure_one()
        payload = {
            "chargeAmount": {
                "amount": self._amazon_pay_format_amount(tx.amount),
                "currencyCode": tx.currency_id.name,
            },
        }
        if self.amazon_pay_soft_descriptor:
            payload["softDescriptor"] = self.amazon_pay_soft_descriptor[:16]
        return self._amazon_pay_request(
            "POST",
            f"checkoutSessions/{checkout_session_id}/complete",
            payload=payload,
            idempotency_key=uuid.uuid4().hex,
        )

    def _amazon_pay_get_checkout_session(self, checkout_session_id):
        self.ensure_one()
        return self._amazon_pay_request(
            "GET", f"checkoutSessions/{checkout_session_id}"
        )

    def _amazon_pay_get_charge(self, charge_id):
        self.ensure_one()
        return self._amazon_pay_request("GET", f"charges/{charge_id}")

    def _amazon_pay_get_refund(self, refund_id):
        self.ensure_one()
        return self._amazon_pay_request("GET", f"refunds/{refund_id}")

    def _amazon_pay_create_refund(self, charge_id, amount, currency):
        self.ensure_one()
        payload = {
            "chargeId": charge_id,
            "refundAmount": {
                "amount": self._amazon_pay_format_amount(amount),
                "currencyCode": currency.name,
            },
        }
        if self.amazon_pay_soft_descriptor:
            payload["softDescriptor"] = self.amazon_pay_soft_descriptor[:16]
        return self._amazon_pay_request(
            "POST",
            "refunds",
            payload=payload,
            idempotency_key=uuid.uuid4().hex,
        )
