from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestPaymentTermRegressions(BaseCommon):
    _test_user_groups = (
        "base.group_user",
        "account.group_account_manager",
        "base.group_system",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.env.ref("base.USD")
        if cls.currency == cls.company.currency_id:
            cls.currency = cls.env.ref("base.EUR")
        cls.currency.active = True
        cls.cash_rounding = cls.env["account.cash.rounding"].create(
            {"name": "Nearest five cents", "rounding": 0.05}
        )

    def _create_term(self, lines, **values):
        return self.env["account.payment.term"].create(
            {
                "name": "Regression payment term",
                "line_ids": [
                    Command.clear(),
                    *[Command.create(line) for line in lines],
                ],
                **values,
            }
        )

    def _compute(self, term, **values):
        arguments = {
            "date_ref": fields.Date.to_date("2026-01-01"),
            "currency": self.currency,
            "company": self.company,
            "tax_amount": 0,
            "tax_amount_currency": 0,
            "sign": 1,
            "untaxed_amount": 200,
            "untaxed_amount_currency": 100,
        }
        arguments.update(values)
        return term._compute_terms(**arguments)

    def _assert_amounts(self, result, expected):
        self.assertEqual(len(result["line_ids"]), len(expected))
        for line, (company_amount, foreign_amount) in zip(
            result["line_ids"], expected, strict=True
        ):
            self.assertAlmostEqual(line["company_amount"], company_amount, places=2)
            self.assertAlmostEqual(line["foreign_amount"], foreign_amount, places=2)

    def test_foreign_currency_percentages(self):
        term = self._create_term(
            [
                {"value": "percent", "value_amount": 30},
                {"value": "percent", "value_amount": 70, "nb_days": 30},
            ]
        )
        for sign in (1, -1):
            with self.subTest(sign=sign):
                result = self._compute(
                    term,
                    sign=sign,
                    untaxed_amount=sign * 200,
                    untaxed_amount_currency=sign * 100,
                )
                self._assert_amounts(
                    result, [(sign * 60, sign * 30), (sign * 140, sign * 70)]
                )

    def test_foreign_currency_fixed_amount(self):
        term = self._create_term(
            [
                {"value": "fixed", "value_amount": 20},
                {"value": "percent", "value_amount": 100},
            ]
        )
        for sign in (1, -1):
            with self.subTest(sign=sign):
                result = self._compute(
                    term,
                    sign=sign,
                    untaxed_amount=sign * 200,
                    untaxed_amount_currency=sign * 100,
                )
                self._assert_amounts(
                    result, [(sign * 40, sign * 20), (sign * 160, sign * 80)]
                )

    def test_cash_rounding_with_foreign_currency(self):
        term = self._create_term(
            [
                {"value": "percent", "value_amount": 30},
                {"value": "percent", "value_amount": 70},
            ]
        )
        result = self._compute(
            term,
            untaxed_amount=200.10,
            untaxed_amount_currency=100.05,
            cash_rounding=self.cash_rounding,
        )
        self._assert_amounts(result, [(60, 30), (140.10, 70.05)])

    def test_custom_rounding_preserves_balance(self):
        term = self._create_term(
            [
                {"value": "percent", "value_amount": 30, "amount_round": 1},
                {"value": "percent", "value_amount": 20},
                {"value": "percent", "value_amount": 50},
            ]
        )
        result = self._compute(term, untaxed_amount=202, untaxed_amount_currency=101)
        self._assert_amounts(result, [(61, 30), (40.40, 20.20), (100.60, 50.80)])

    def test_untaxed_percentage_with_cash_rounding(self):
        term = self._create_term(
            [
                {"value": "percent_amount_untaxed", "value_amount": 30},
                {"value": "percent", "value_amount": 100},
            ]
        )
        result = self._compute(
            term,
            currency=self.company.currency_id,
            tax_amount=20.03,
            tax_amount_currency=20.03,
            untaxed_amount=100.02,
            untaxed_amount_currency=100.02,
            cash_rounding=self.cash_rounding,
        )
        self._assert_amounts(result, [(30, 30), (90.05, 90.05)])

    def test_early_discount_with_cash_rounding(self):
        term = self._create_term(
            [{"value": "percent", "value_amount": 100}],
            early_discount=True,
            discount_percentage=2,
            discount_days=10,
        )
        result = self._compute(
            term,
            untaxed_amount=200.10,
            untaxed_amount_currency=100.05,
            cash_rounding=self.cash_rounding,
        )
        self.assertAlmostEqual(result["discount_amount_currency"], 98.05, places=2)
        self.assertAlmostEqual(result["discount_balance"], 196.10, places=2)
        self._assert_amounts(result, [(200.10, 100.05)])

    def test_unsaved_holiday_and_sequential_dates(self):
        date_ref = fields.Date.to_date("2026-01-01")
        term = self.env["account.payment.term"].new(
            {
                "name": "Unsaved holidays",
                "sequential_lines": True,
                "line_ids": [
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 30,
                            "delay_type": "days_after",
                            "nb_days": 0,
                        }
                    ),
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 70,
                            "delay_type": "days_after",
                            "nb_days": 10,
                        }
                    ),
                ],
                "holiday_ids": [
                    Command.create(
                        {"holiday": date_ref, "date_postponed": "2026-01-05"}
                    )
                ],
            }
        )
        result = self._compute(term)
        self.assertEqual(
            [line["date"] for line in result["line_ids"]],
            [fields.Date.to_date("2026-01-05"), fields.Date.to_date("2026-01-15")],
        )

    def test_holiday_changes_update_unsaved_preview(self):
        with Form(self.env["account.payment.term"]) as form:
            form.name = "Holiday preview"
            form.example_date = "2026-01-01"
            with form.holiday_ids.new() as holiday:
                holiday.holiday = "2026-01-01"
                holiday.date_postponed = "2026-01-05"
            preview = form.example_preview
            with form.holiday_ids.edit(0) as holiday:
                holiday.date_postponed = "2026-01-06"
            self.assertNotEqual(form.example_preview, preview)

    def test_duplicate_holiday_preview_and_validation(self):
        form = Form(self.env["account.payment.term"])
        form.name = "Duplicate holiday preview"
        form.example_date = "2026-01-01"
        with form.holiday_ids.new() as holiday:
            holiday.holiday = "2026-01-01"
            holiday.date_postponed = "2026-01-05"
        preview = form.example_preview
        with form.holiday_ids.new() as holiday:
            holiday.holiday = "2026-01-01"
            holiday.date_postponed = "2026-01-06"
        self.assertEqual(form.example_preview, preview)
        with (
            self.assertRaisesRegex(ValidationError, "is duplicated"),
            self.env.cr.savepoint(),
        ):
            form.save()
