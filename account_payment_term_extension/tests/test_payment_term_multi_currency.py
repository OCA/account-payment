# Copyright 2026 Juan Jara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentTermMultiCurrency(AccountTestInvoicingCommon):
    """Percentage lines must take the company amount from the company
    currency total and the foreign amount from the document currency total.

    Swapping them made the company residual overshoot, so the balance line
    ended up with company_amount and foreign_amount of opposite signs, which
    the DB constraint account_move_line_check_amount_currency_balance_sign
    rejects.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_currency = cls.env.company.currency_id
        cls.foreign_currency = cls.setup_other_currency(
            "EUR" if cls.company_currency.name != "EUR" else "USD",
            rates=[("2020-01-01", 5.0)],
        )
        # 30% on issue date, the rest as balance
        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "30% now, balance at 30 days",
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 30.0, "nb_days": 0}
                    ),
                    Command.create(
                        {"value": "percent", "value_amount": 70.0, "nb_days": 30}
                    ),
                ],
            }
        )

    def test_compute_terms_percent_multi_currency(self):
        """1000 in foreign currency at rate 5.0 is 200 in company currency."""
        res = self.payment_term._compute_terms(
            date_ref=fields.Date.from_string("2024-01-01"),
            currency=self.foreign_currency,
            company=self.env.company,
            tax_amount=0.0,
            tax_amount_currency=0.0,
            sign=1,
            untaxed_amount=200.0,
            untaxed_amount_currency=1000.0,
        )
        first_line, balance_line = res["line_ids"]
        self.assertEqual(first_line["company_amount"], 60.0)
        self.assertEqual(first_line["foreign_amount"], 300.0)
        self.assertEqual(balance_line["company_amount"], 140.0)
        self.assertEqual(balance_line["foreign_amount"], 700.0)

    def test_invoice_percent_multi_currency(self):
        """Posting the invoice used to break the amount_currency sign check."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2024-01-01",
                "date": "2024-01-01",
                "currency_id": self.foreign_currency.id,
                "invoice_payment_term_id": self.payment_term.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "test line",
                            "quantity": 1.0,
                            "price_unit": 1000.0,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")
        self.assertEqual(len(term_lines), 2)
        self.assertEqual(term_lines.mapped("amount_currency"), [300.0, 700.0])
        self.assertEqual(term_lines.mapped("balance"), [60.0, 140.0])
