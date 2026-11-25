# Copyright 2026 OmniaSolutions - Matteo Boscolo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Amounts of the payment term lines in company and in foreign currency.

The module overrides ``_compute_terms`` completely: for every configuration
that standard Odoo also supports, the result must be the same as the standard
computation, in both currencies.
"""

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.account.models.account_payment_term import (
    AccountPaymentTerm as StandardAccountPaymentTerm,
)
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

# Foreign currency units for 1 company currency unit (as on the customer
# database: 1 CHF = 1.059434 EUR)
FOREIGN_RATE = 1.059434

PERCENT_SPLITS = [
    [100.0],
    [50.0, 50.0],
    [30.0, 70.0],
    [70.0, 30.0],
    [20.0, 80.0],
    [15.0, 85.0],
    [40.0, 30.0, 30.0],
    [50.0, 25.0, 25.0],
    [33.333333, 33.333333, 33.333334],
    [25.0, 25.0, 25.0, 25.0],
]

TOTALS = [10000.0, 7000.0, 45700.0, 73000.0, 290.0, 1234.57, 99999.99, 0.05]

DELAYS = [
    ("days_after", 30),
    ("days_after_end_of_month", 30),
    ("days_after_end_of_next_month", 10),
    ("days_end_of_month_on_the", 60),
]


@tagged("post_install", "-at_install")
class TestPaymentTermCurrency(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company_currency = cls.company.currency_id
        cls.foreign_currency = cls.setup_other_currency(
            "EUR" if cls.company_currency.name != "EUR" else "CHF",
            rates=[("1900-01-01", FOREIGN_RATE)],
        )
        cls.date_ref = fields.Date.to_date("2026-09-22")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def _create_term(cls, lines, **values):
        """lines: list of (value, value_amount, delay_type, nb_days)."""
        return cls.env["account.payment.term"].create(
            {
                "name": "Test term",
                "line_ids": [
                    Command.create(
                        {
                            "value": value,
                            "value_amount": value_amount,
                            "delay_type": delay_type,
                            "nb_days": nb_days,
                        }
                    )
                    for value, value_amount, delay_type, nb_days in lines
                ],
                **values,
            }
        )

    def _percent_term(self, split, delay_type="days_after", nb_days=30, **values):
        return self._create_term(
            [
                ("percent", amount, delay_type, nb_days * (i + 1))
                for i, amount in enumerate(split)
            ],
            **values,
        )

    def _amounts(self, currency, total_currency, sign=1, tax_ratio=0.0):
        """Arguments of _compute_terms for a move total in ``currency``."""
        total_currency = sign * total_currency
        tax_currency = currency.round(total_currency * tax_ratio)
        untaxed_currency = total_currency - tax_currency
        rate = FOREIGN_RATE if currency != self.company_currency else 1.0
        return {
            "date_ref": self.date_ref,
            "currency": currency,
            "company": self.company,
            "tax_amount": self.company_currency.round(tax_currency / rate),
            "tax_amount_currency": tax_currency,
            "sign": sign,
            "untaxed_amount": self.company_currency.round(untaxed_currency / rate),
            "untaxed_amount_currency": untaxed_currency,
        }

    def _compare_with_standard(self, term, kwargs):
        result = term._compute_terms(**kwargs)
        expected = StandardAccountPaymentTerm._compute_terms(term, **kwargs)
        currency = kwargs["currency"]
        self.assertEqual(len(result["line_ids"]), len(expected["line_ids"]))
        for line, expected_line in zip(
            result["line_ids"], expected["line_ids"], strict=True
        ):
            self.assertEqual(line["date"], expected_line["date"])
            self.assertAlmostEqual(
                line["foreign_amount"],
                expected_line["foreign_amount"],
                places=currency.decimal_places,
                msg="Wrong amount in the move currency",
            )
            self.assertAlmostEqual(
                line["company_amount"],
                expected_line["company_amount"],
                places=self.company_currency.decimal_places,
                msg="Wrong amount in the company currency",
            )
        for key in ("discount_percentage", "discount_date", "discount_balance"):
            self.assertEqual(result[key], expected[key], key)
        if "discount_amount_currency" in expected:
            self.assertAlmostEqual(
                result["discount_amount_currency"],
                expected["discount_amount_currency"],
            )
        self._check_totals(result, kwargs)
        return result

    def _check_totals(self, result, kwargs):
        total_currency = (
            kwargs["tax_amount_currency"] + kwargs["untaxed_amount_currency"]
        )
        total = kwargs["tax_amount"] + kwargs["untaxed_amount"]
        self.assertAlmostEqual(
            sum(line["foreign_amount"] for line in result["line_ids"]), total_currency
        )
        self.assertAlmostEqual(
            sum(line["company_amount"] for line in result["line_ids"]), total
        )

    # ------------------------------------------------------------------
    # _compute_terms against the standard computation
    # ------------------------------------------------------------------
    def test_percent_matches_standard(self):
        for currency in (self.company_currency, self.foreign_currency):
            for sign in (1, -1):
                for split in PERCENT_SPLITS:
                    term = self._percent_term(split)
                    for total in TOTALS:
                        for tax_ratio in (0.0, 0.077, 0.22):
                            with self.subTest(
                                currency=currency.name,
                                sign=sign,
                                split=split,
                                total=total,
                                tax_ratio=tax_ratio,
                            ):
                                self._compare_with_standard(
                                    term,
                                    self._amounts(currency, total, sign, tax_ratio),
                                )

    def test_percent_line_amounts_foreign_currency(self):
        """The customer case: 10'000 EUR, 30/60 days, 50% + 50%."""
        term = self._percent_term([50.0, 50.0])
        kwargs = self._amounts(self.foreign_currency, 10000.0)
        result = self._compare_with_standard(term, kwargs)
        total_company = kwargs["untaxed_amount"]
        self.assertEqual(
            [line["foreign_amount"] for line in result["line_ids"]], [5000.0, 5000.0]
        )
        half = self.company_currency.round(total_company / 2)
        self.assertEqual(
            [line["company_amount"] for line in result["line_ids"]],
            [half, total_company - half],
        )

    def test_percent_each_line_is_its_share(self):
        for split in PERCENT_SPLITS:
            term = self._percent_term(split)
            for total in TOTALS:
                with self.subTest(split=split, total=total):
                    kwargs = self._amounts(self.foreign_currency, total)
                    result = term._compute_terms(**kwargs)
                    for line, percent in zip(
                        result["line_ids"][:-1], split[:-1], strict=True
                    ):
                        self.assertAlmostEqual(
                            line["foreign_amount"],
                            self.foreign_currency.round(total * percent / 100),
                        )
                        self.assertAlmostEqual(
                            line["company_amount"],
                            self.company_currency.round(
                                kwargs["untaxed_amount"] * percent / 100
                            ),
                        )
                    self._check_totals(result, kwargs)

    def test_delay_types_match_standard(self):
        for delay_type, nb_days in DELAYS:
            for currency in (self.company_currency, self.foreign_currency):
                with self.subTest(delay_type=delay_type, currency=currency.name):
                    term = self._percent_term(
                        [50.0, 50.0], delay_type=delay_type, nb_days=nb_days
                    )
                    self._compare_with_standard(term, self._amounts(currency, 10000.0))

    def test_fixed_matches_standard(self):
        layouts = [
            [("fixed", 1000.0), ("percent", 100.0)],
            [("fixed", 1000.0), ("fixed", 2500.0), ("percent", 100.0)],
            [("percent", 30.0), ("fixed", 1500.0), ("percent", 70.0)],
            [("fixed", 0.0), ("percent", 100.0)],
        ]
        # Only in company currency: fixed amounts are not converted at the
        # currency rate yet, which is a separate issue
        for sign in (1, -1):
            for layout in layouts:
                with self.subTest(sign=sign, layout=layout):
                    term = self._create_term(
                        [
                            (value, amount, "days_after", 30 * i)
                            for i, (value, amount) in enumerate(layout)
                        ]
                    )
                    self._compare_with_standard(
                        term,
                        self._amounts(self.company_currency, 10000.0, sign, 0.077),
                    )

    def test_early_discount_matches_standard(self):
        for computation in ("included", "excluded", "mixed"):
            for currency in (self.company_currency, self.foreign_currency):
                with self.subTest(computation=computation, currency=currency.name):
                    term = self._percent_term(
                        [100.0],
                        early_discount=True,
                        discount_percentage=2.0,
                        discount_days=10,
                        early_pay_discount_computation=computation,
                    )
                    self._compare_with_standard(
                        term, self._amounts(currency, 10000.0, 1, 0.077)
                    )

    def test_sequential_lines_amounts(self):
        """Sequential lines only move the dates, never the amounts."""
        term = self._percent_term([50.0, 50.0], sequential_lines=True)
        kwargs = self._amounts(self.foreign_currency, 10000.0)
        result = term._compute_terms(**kwargs)
        self.assertEqual(
            [line["foreign_amount"] for line in result["line_ids"]], [5000.0, 5000.0]
        )
        self.assertEqual(
            [line["date"] for line in result["line_ids"]],
            [fields.Date.to_date("2026-10-22"), fields.Date.to_date("2026-12-21")],
        )
        self._check_totals(result, kwargs)

    # ------------------------------------------------------------------
    # Features of this module only
    # ------------------------------------------------------------------
    def test_amount_round(self):
        term = self._percent_term([30.0, 70.0])
        term.line_ids[0].amount_round = 100.0
        kwargs = self._amounts(self.company_currency, 10010.0)
        result = term._compute_terms(**kwargs)
        first = result["line_ids"][0]
        # 30% of 10'010 = 3'003, rounded to a multiple of 100
        self.assertEqual(first["foreign_amount"], 3000.0)
        self.assertEqual(first["company_amount"], 3000.0)
        self._check_totals(result, kwargs)

    def test_percent_amount_untaxed(self):
        term = self._create_term(
            [
                ("percent_amount_untaxed", 50.0, "days_after", 0),
                ("percent", 100.0, "days_after", 30),
            ]
        )
        kwargs = self._amounts(self.company_currency, 1220.0, 1, 220.0 / 1220.0)
        result = term._compute_terms(**kwargs)
        first, last = result["line_ids"]
        self.assertEqual(first["foreign_amount"], 500.0)
        self.assertEqual(first["company_amount"], 500.0)
        self.assertEqual(last["foreign_amount"], 720.0)
        self._check_totals(result, kwargs)
        with self.assertRaises(UserError):
            term._compute_terms(**self._amounts(self.foreign_currency, 1220.0))

    # ------------------------------------------------------------------
    # Posted moves
    # ------------------------------------------------------------------
    def _check_move(self, move, split):
        term_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")
        self.assertEqual(len(term_lines), len(split))
        total_currency = sum(term_lines.mapped("amount_currency"))
        total = sum(term_lines.mapped("balance"))
        self.assertAlmostEqual(abs(total_currency), move.amount_total)
        self.assertAlmostEqual(abs(total), abs(move.amount_total_signed))
        for line, percent in zip(term_lines[:-1], split[:-1], strict=True):
            self.assertAlmostEqual(
                line.amount_currency,
                move.currency_id.round(total_currency * percent / 100),
            )
            self.assertAlmostEqual(
                line.balance, self.company_currency.round(total * percent / 100)
            )

    def test_posted_moves(self):
        for move_type in ("out_invoice", "out_refund", "in_invoice", "in_refund"):
            for currency in (self.company_currency, self.foreign_currency):
                for split in (
                    [50.0, 50.0],
                    [33.333333, 33.333333, 33.333334],
                    [30.0, 70.0],
                ):
                    with self.subTest(
                        move_type=move_type, currency=currency.name, split=split
                    ):
                        move = self._create_invoice(
                            move_type=move_type,
                            invoice_date=self.date_ref,
                            currency_id=currency.id,
                            invoice_payment_term_id=self._percent_term(split).id,
                            invoice_line_ids=[
                                Command.create(
                                    {
                                        "name": "line",
                                        "quantity": 1,
                                        "price_unit": 10000.0,
                                        "tax_ids": [Command.clear()],
                                    }
                                )
                            ],
                            post=True,
                        )
                        self._check_move(move, split)
