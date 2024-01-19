# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Command, Date
from odoo.tests.common import TransactionCase


class TestAccountCashDiscountPayment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.AccountMove = cls.env["account.move"]
        cls.PaymentLineCreate = cls.env["account.payment.line.create"]
        cls.PaymentOrder = cls.env["account.payment.order"]
        cls.Journal = cls.env["account.journal"]
        cls.Account = cls.env["account.account"]

        cls.payment_mode_out = cls.env.ref(
            "account_payment_mode.payment_mode_outbound_ct1"
        )
        cls.bank_ing = cls.env.ref("base.bank_ing")
        cls.partner_bank_ing = cls.env.ref("base_iban.bank_iban_main_partner")

        cls.bank_ing_journal = cls.Journal.create(
            {
                "name": "ING Bank",
                "code": "ING-B",
                "type": "bank",
                "bank_id": cls.bank_ing.id,
            }
        )
        cls.company = cls.env.ref("base.main_company")
        cls.company.early_pay_discount_computation = "included"
        cls.purchase_journal = cls.Journal.create(
            {
                "name": "Purchase journal",
                "type": "purchase",
                "code": "PUR",
                "company_id": cls.company.id,
            }
        )
        cls.partner = cls.env.ref("base.res_partner_2")

        cls.account_expense = cls.Account.create(
            {
                "account_type": "expense",
                "company_id": cls.company.id,
                "name": "Test expense",
                "code": "TE.1",
                "reconcile": True,
            }
        )

        cls.early_pay_25_percents_10_days = cls.env["account.payment.term"].create(
            {
                "name": "25% discount if paid within 10 days",
                "company_id": cls.company.id,
                "line_ids": [
                    Command.create(
                        {
                            "value": "balance",
                            "days": 0,
                            "discount_percentage": 25,
                            "discount_days": 10,
                        }
                    )
                ],
            }
        )

        cls.precision = cls.env["decimal.precision"].precision_get("Account")

    def _create_supplier_invoice(self, ref, price_unit=100.0):
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "move_type": "in_invoice",
                "ref": ref,
                "date": Date.today(),
                "invoice_date": Date.today(),
                "invoice_payment_term_id": self.early_pay_25_percents_10_days.id,
                "payment_mode_id": self.payment_mode_out.id,
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "product_id": self.env.ref("product.product_product_4").id,
                            "quantity": 1.0,
                            "price_unit": price_unit,
                            "name": "product that cost 100",
                            "account_id": self.account_expense.id,
                        },
                    )
                ],
            }
        )

        return invoice

    def _create_supplier_refund(self, ref, price_unit=100.0):
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "move_type": "in_refund",
                "ref": ref,
                "date": Date.today(),
                "invoice_date": Date.today(),
                "invoice_payment_term_id": self.early_pay_25_percents_10_days.id,
                "payment_mode_id": self.payment_mode_out.id,
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "product_id": self.env.ref("product.product_product_4").id,
                            "quantity": 1.0,
                            "price_unit": price_unit,
                            "name": "product that cost 100",
                            "account_id": self.account_expense.id,
                        },
                    )
                ],
            }
        )

        return invoice

    def test_invoice_payment_discount(self):
        invoice_date = Date.today()
        invoice = self._create_supplier_invoice("test-ref")
        invoice.action_post()

        payment_order = self.PaymentOrder.create(
            {"payment_mode_id": self.payment_mode_out.id, "payment_type": "outbound"}
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "target_move": "posted",
            }
        )
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        move_lines = payment_line_wizard.move_line_ids
        self.assertEqual(len(move_lines), 1)

        move_line = move_lines[0]
        # 115 - 25%
        self.assertAlmostEqual(move_line.discount_amount_currency, -86.25, 2)

        payment_line_wizard.create_payment_lines()

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 86.25)

        # Change the amount of the line and trigger the onchange amount method
        # and verify there is a warning
        payment_line.amount_currency = 125
        onchange_res = payment_line._onchange_amount_with_discount()
        self.assertTrue("warning" in onchange_res)
        self.assertFalse(payment_line.pay_with_discount)

        # Change it back to use the discount
        payment_line.toggle_pay_with_discount()
        self.assertAlmostEqual(payment_line.amount_currency, 86.25)

        # Change pay_with_discount and check if discount amount is coherent
        # with the invoice
        payment_line.toggle_pay_with_discount()
        self.assertEqual(payment_line.amount_currency, invoice.amount_total)

        payment_line.toggle_pay_with_discount()
        self.assertEqual(
            payment_line.amount_currency,
            payment_line.move_line_id.discount_amount_currency * -1,
        )

        self.assertAlmostEqual(payment_line.discount_amount, 28.75, self.precision)
        self.assertAlmostEqual(payment_line.amount_currency, 86.25, self.precision)

    def test_invoice_payment_refund_and_discount(self):
        """
        Try to do a payment when there is a refund
        The refund should be taken into account on payment
        And the discount is computed after taking into account the refund
        """
        invoice_date = Date.today()
        invoice = self._create_supplier_invoice("test-ref", 100.0)
        invoice.action_post()

        refund = self._create_supplier_refund("test-refund", 20.0)
        refund.action_post()

        (refund + invoice).line_ids.filtered(
            lambda x: x.account_id.account_type == "liability_payable"
        ).reconcile()

        payment_order = self.PaymentOrder.create(
            {"payment_mode_id": self.payment_mode_out.id, "payment_type": "outbound"}
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "target_move": "posted",
            }
        )
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        move_lines = payment_line_wizard.move_line_ids
        self.assertEqual(len(move_lines), 1)

        payment_line_wizard.create_payment_lines()

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)

        # 115 - 23 (from refund) = 92 * 0.75 (discount) = 69
        self.assertAlmostEqual(payment_line.amount_currency, 69)

        # Change the amount of the line and trigger the onchange amount method
        # and verify there is a warning
        payment_line.amount_currency = 100
        onchange_res = payment_line._onchange_amount_with_discount()
        self.assertTrue("warning" in onchange_res)
        self.assertFalse(payment_line.pay_with_discount)

        # Change it back to use the discount
        payment_line.toggle_pay_with_discount()
        self.assertAlmostEqual(payment_line.amount_currency, 69)

        # Change pay_with_discount and check if discount amount is coherent
        # with the invoice
        payment_line.toggle_pay_with_discount()
        self.assertEqual(payment_line.amount_currency, invoice.amount_residual)

        payment_line.toggle_pay_with_discount()
        self.assertEqual(
            payment_line.amount_currency,
            payment_line.move_line_id.amount_residual * 0.75 * -1,  # discount of 25
        )

        self.assertAlmostEqual(payment_line.discount_amount, 23.00, self.precision)
        self.assertAlmostEqual(payment_line.amount_currency, 69.00, self.precision)

    def test_toggle_pay_with_discount_allowed(self):
        invoice_date = Date.today()
        invoice = self._create_supplier_invoice("test-ref", 100.0)
        invoice.action_post()

        payment_order = self.PaymentOrder.create(
            {"payment_mode_id": self.payment_mode_out.id, "payment_type": "outbound"}
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "target_move": "posted",
            }
        )
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        move_lines = payment_line_wizard.move_line_ids
        self.assertEqual(len(move_lines), 1)

        payment_line_wizard.create_payment_lines()

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertTrue(payment_line.toggle_pay_with_discount_allowed)

        payment_order.action_cancel()

        self.assertEqual(payment_order.state, "cancel")
        self.assertFalse(payment_line.toggle_pay_with_discount_allowed)
