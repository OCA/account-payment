from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.common import PaymentCommon

PROVIDER = "odoo.addons.payment_amazon_pay.models.payment_provider.PaymentProvider"


@tagged("post_install", "-at_install")
class TestPaymentAmazonPay(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_key_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        cls.provider = cls._prepare_provider(
            "amazon_pay",
            update_values={
                "amazon_pay_merchant_id": "A1TESTMERCHANT",
                "amazon_pay_store_id": "amzn1.application-oa2-client.test",
                "amazon_pay_public_key_id": "SANDBOX-TESTPUBLICKEYID",
                "amazon_pay_private_key": private_key_pem,
                "amazon_pay_region": "eu",
                "amazon_pay_checkout_language": "es_ES",
            },
        )
        cls.payment_method_id = cls.env.ref("payment.payment_method_amazon_pay").id
        cls.currency = cls.currency_euro

    def _completed_session(self, reference, amount, currency="EUR", session="S-1"):
        return {
            "checkoutSessionId": session,
            "chargePermissionId": f"CP-{session}",
            "chargeId": f"CP-{session}-C1",
            "statusDetails": {"state": "Completed"},
            "paymentDetails": {
                "chargeAmount": {"amount": f"{amount:.2f}", "currencyCode": currency}
            },
            "merchantMetadata": {"merchantReferenceId": reference},
            "_http_status": 200,
        }

    def _return(self, tx, session_data, session_id="S-1"):
        with (
            patch(PROVIDER + "._amazon_pay_request", return_value=session_data),
            mute_logger("odoo.addons.payment_amazon_pay.models.payment_transaction"),
        ):
            self.env["payment.transaction"]._handle_notification_data(
                "amazon_pay",
                {"reference": tx.reference, "checkoutSessionId": session_id},
            )
        tx.invalidate_recordset()

    def test_processing_values(self):
        tx = self._create_transaction("redirect")
        cfg = tx._get_processing_values()["amazon_pay_cfg"]
        self.assertEqual(cfg["merchantId"], "A1TESTMERCHANT")
        self.assertEqual(cfg["ledgerCurrency"], self.currency.name)
        self.assertEqual(
            set(cfg["createCheckoutSessionConfig"]),
            {"payloadJSON", "signature", "publicKeyId"},
        )

    def test_matching_session_confirms_the_transaction(self):
        tx = self._create_transaction("redirect", reference="LEGIT")
        self._return(tx, self._completed_session("LEGIT", tx.amount))
        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.amazon_pay_charge_id, "CP-S-1-C1")

    def test_foreign_session_does_not_confirm_the_transaction(self):
        tx = self._create_transaction("redirect", reference="EXPENSIVE")
        session = self._completed_session("CHEAP", 1.0, session="S-CHEAP")
        self._return(tx, session, session_id="S-CHEAP")
        self.assertNotEqual(tx.state, "done")
        self.assertFalse(tx.amazon_pay_charge_id)

    def test_amount_mismatch_does_not_confirm_the_transaction(self):
        tx = self._create_transaction("redirect", reference="TAMPERED")
        self.assertNotEqual(tx.amount, 1.0)
        self._return(tx, self._completed_session("TAMPERED", 1.0))
        self.assertNotEqual(tx.state, "done")
        self.assertFalse(tx.amazon_pay_charge_id)
