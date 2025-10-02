from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.payment.tests.common import PaymentCommon


@tagged("-at_install", "post_install")
class TestAccountPaymentRegister(AccountTestInvoicingCommon, PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountPaymentRegister = cls.env["account.payment.register"]
        cls.PaymentMethod = cls.env["account.payment.method"]
        cls.PaymentMethodLine = cls.env["account.payment.method.line"]
        cls.AccountAccount = cls.env["account.account"]
        cls.payment_account = cls.AccountAccount.create(
            {
                "name": "Test Payment Account",
                "code": "TEST.ACC",
                "account_type": "asset_cash",
            }
        )
        cls.payment_method = cls.PaymentMethod.sudo().create(
            {
                "name": "Test Method",
                "code": "test_method",
                "payment_type": "outbound",
            }
        )
        cls.payment_method_line_with_acc = cls.PaymentMethodLine.sudo().create(
            {
                "name": "Method with Account",
                "payment_method_id": cls.payment_method.id,
                "payment_account_id": cls.payment_account.id,
                "payment_type": "outbound",
                "company_id": cls.env.company.id,
            }
        )
        cls.payment_method_line_without_acc = cls.PaymentMethodLine.sudo().create(
            {
                "name": "Method without Account",
                "payment_method_id": cls.payment_method.id,
                "payment_type": "outbound",
                "company_id": cls.env.company.id,
            }
        )
        cls.out_invoice_1 = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "date": "2017-01-01",
                "invoice_date": "2017-01-01",
                "partner_id": cls.partner_a.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_a.id,
                            "price_unit": 1000.0,
                            "tax_ids": [],
                        },
                    )
                ],
            }
        )

    def test_require_payment_account_compute(self):
        """It should require a payment account only if payment method has no account."""

        wizard = self.AccountPaymentRegister.new(
            {
                "payment_method_line_id": self.payment_method_line_without_acc.id,
            }
        )
        wizard._compute_require_payment_account()
        self.assertTrue(wizard.require_payment_account)

        wizard_with_acc = self.AccountPaymentRegister.new(
            {
                "payment_method_line_id": self.payment_method_line_with_acc.id,
            }
        )
        wizard_with_acc._compute_require_payment_account()
        self.assertFalse(wizard_with_acc.require_payment_account)

    def test_create_payment_vals_with_custom_account(self):
        """When require_payment_account=True and payment_account_id is set,
        it should add outstanding_account_id to payment vals."""
        active_ids = self.out_invoice_1.ids
        wizard = self.AccountPaymentRegister.with_context(
            active_model="account.move", active_ids=active_ids
        ).create(
            {
                "payment_method_line_id": self.payment_method_line_without_acc.id,
                "payment_account_id": self.payment_account.id,
            }
        )
        wizard._compute_require_payment_account()
        batch_result = self.env["account.payment"].new({})  # dummy batch result

        vals = wizard._create_payment_vals_from_wizard(batch_result)
        self.assertEqual(vals.get("outstanding_account_id"), self.payment_account.id)
        payments = wizard._create_payments()
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments.outstanding_account_id, self.payment_account)

    def test_create_payment_vals_without_custom_account(self):
        """If require_payment_account=False,
        no outstanding_account_id should be added."""
        active_ids = self.out_invoice_1.ids
        wizard = self.AccountPaymentRegister.with_context(
            active_model="account.move", active_ids=active_ids
        ).create(
            {
                "payment_method_line_id": self.payment_method_line_with_acc.id,
            }
        )
        wizard._compute_require_payment_account()
        batch_result = self.env["account.payment"].new({})  # dummy batch result

        vals = wizard._create_payment_vals_from_wizard(batch_result)
        self.assertNotIn("outstanding_account_id", vals)
