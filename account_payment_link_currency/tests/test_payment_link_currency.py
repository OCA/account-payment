# Copyright 2026 volkantasci
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from werkzeug import urls

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.payment import utils as payment_utils


@tagged("post_install", "-at_install")
class TestPaymentLinkCurrency(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_currency = cls.company_data["currency"]
        cls.foreign_currency = cls.setup_other_currency(
            "EUR", rounding=0.01, rates=[("2026-01-01", 0.5)]
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "currency_id": cls.foreign_currency.id,
                "invoice_date": "2026-01-15",
                "date": "2026-01-15",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Consulting Service",
                            "quantity": 1.0,
                            "price_unit": 1000.0,
                            "tax_ids": [],
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()

    def test_default_currency_keeps_standard_portal_link(self):
        wizard = (
            self.env["payment.link.wizard"]
            .with_context(
                active_id=self.invoice.id,
                active_model="account.move",
            )
            .create({})
        )
        self.assertEqual(wizard.currency_id, self.foreign_currency)
        self.assertAlmostEqual(wizard.amount, 1000.0)
        self.assertIn(f"move_id={self.invoice.id}", wizard.link)
        self.assertIn("#portal_pay", wizard.link)

    def test_onchange_currency_converts_amount_and_uses_payment_pay_route(self):
        wizard = (
            self.env["payment.link.wizard"]
            .with_context(
                active_id=self.invoice.id,
                active_model="account.move",
            )
            .create({"amount": 500.0})
        )
        wizard.currency_id = self.company_currency
        wizard._onchange_currency_id()

        # 1000 EUR at rate 0.5 = 2000 company currency; 500 EUR = 1000 company currency
        self.assertAlmostEqual(wizard.amount_max, 2000.0)
        self.assertAlmostEqual(wizard.amount, 1000.0)
        self.assertIn("/payment/pay?", wizard.link)

        parsed = urls.url_parse(wizard.link)
        params = urls.url_decode(parsed.query)
        self.assertEqual(int(params["currency_id"]), self.company_currency.id)
        self.assertAlmostEqual(float(params["amount"]), 1000.0)
        self.assertEqual(
            params["access_token"],
            payment_utils.generate_access_token(
                self.partner_a.id,
                1000.0,
                self.company_currency.id,
                env=self.env,
            ),
        )

    def test_transaction_auto_links_invoice_by_reference(self):
        provider = self.env["payment.provider"].with_context(active_test=False).search(
            [], limit=1
        ) or self.env["payment.provider"].create({"name": "Test Provider"})
        payment_method = self.env["payment.method"].with_context(
            active_test=False
        ).search([], limit=1) or self.env["payment.method"].create(
            {"name": "Test Method", "code": "test_method"}
        )
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": provider.id,
                "payment_method_id": payment_method.id,
                "reference": f"{self.invoice.name}-1",
                "amount": 1000.0,
                "currency_id": self.company_currency.id,
                "partner_id": self.partner_a.id,
            }
        )
        self.assertEqual(tx.invoice_ids, self.invoice)
        tx._set_done()
        self.invoice.invalidate_recordset(["amount_paid"])
        self.assertAlmostEqual(self.invoice.amount_paid, 500.0)

        # Test mixed transactions and non-existent partner
        third_currency = self.setup_other_currency(
            "GBP", rounding=0.01, rates=[("2026-01-01", 0.25)]
        )
        tx_same = self.env["payment.transaction"].create(
            {
                "provider_id": provider.id,
                "payment_method_id": payment_method.id,
                "reference": f"{self.invoice.name}-2",
                "amount": 100.0,
                "currency_id": self.foreign_currency.id,
                "partner_id": self.partner_a.id,
                "invoice_ids": [Command.set(self.invoice.ids)],
            }
        )
        tx_same._set_done()
        tx_third = self.env["payment.transaction"].create(
            {
                "provider_id": provider.id,
                "payment_method_id": payment_method.id,
                "reference": f"{self.invoice.name}-3",
                "amount": 50.0,
                "currency_id": third_currency.id,
                "partner_id": self.partner_a.id,
                "invoice_ids": [Command.set(self.invoice.ids)],
            }
        )
        tx_third._set_done()
        self.invoice.invalidate_recordset(["amount_paid"])
        self.assertGreater(self.invoice.amount_paid, 600.0)

        empty_move = self.env["payment.transaction"]._find_invoice_from_reference(
            self.invoice.name, -999999
        )
        self.assertFalse(empty_move)

    def test_create_with_currency_and_conversion_edge_cases(self):
        third_currency = self.setup_other_currency(
            "CHF", rounding=0.01, rates=[("2026-01-01", 0.5)]
        )
        wizard = (
            self.env["payment.link.wizard"]
            .with_context(
                active_id=self.invoice.id,
                active_model="account.move",
            )
            .create({"currency_id": self.company_currency.id})
        )
        self.assertAlmostEqual(wizard.amount_max, 2000.0)
        self.assertAlmostEqual(wizard.amount, 2000.0)
        self.assertEqual(wizard.previous_currency_id, self.company_currency)

        # Convert back to foreign_currency via onchange, plus open_installments
        wizard.open_installments = [{"amount": 1000.0, "number": 1}]
        wizard.currency_id = self.foreign_currency
        wizard._onchange_currency_id()
        self.assertAlmostEqual(wizard.amount, 1000.0)
        self.assertAlmostEqual(wizard.open_installments[0]["amount"], 500.0)

        # Onchange when previous_currency_id is cleared
        wizard.previous_currency_id = False
        wizard.currency_id = self.company_currency
        wizard._onchange_currency_id()
        self.assertEqual(wizard.previous_currency_id, self.company_currency)

        # Edge cases in _convert_document_amount
        self.assertEqual(
            wizard._convert_document_amount(
                0.0, self.foreign_currency, self.company_currency
            ),
            0.0,
        )
        # Third currency conversion on account.move
        converted_third = wizard._convert_document_amount(
            100.0, self.foreign_currency, third_currency
        )
        self.assertAlmostEqual(converted_third, 100.0)

        # Non-account.move fallback conversion
        wizard.res_model = "res.partner"
        wizard.res_id = 0
        converted_fallback = wizard._convert_document_amount(
            100.0, self.foreign_currency, self.company_currency
        )
        self.assertAlmostEqual(converted_fallback, 200.0)
