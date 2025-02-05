from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestAccountPaymentTermMultiDay(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_term_model = cls.env["account.payment.term"]
        cls.invoice_model = cls.env["account.move"]
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.payment_term_0_day_5 = cls.payment_term_model.create(
            {
                "name": "Normal payment in day 5",
                "active": True,
                "line_ids": [
                    fields.Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "nb_days": 5,
                            "payment_days": "5",
                        },
                    ),
                ],
            }
        )
        cls.payment_term_0_days_5_10 = cls.payment_term_model.create(
            {
                "name": "Payment for days 5 and 10",
                "active": True,
                "line_ids": [
                    fields.Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "nb_days": 0,
                            "payment_days": "5,10",
                        },
                    ),
                ],
            }
        )
        cls.payment_term_0_days_15_20_then_5_10 = cls.payment_term_model.create(
            {
                "name": "Payment for days 15 and 20 then 5 and 10",
                "active": True,
                "sequential_lines": True,
                "line_ids": [
                    fields.Command.create(
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "nb_days": 0,
                            "payment_days": "15,20",
                        },
                    ),
                    fields.Command.create(
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "nb_days": 0,
                            "payment_days": "10-5",
                        },
                    ),
                ],
            }
        )
        cls.payment_term_round = cls.payment_term_model.create(
            {
                "name": "Payment for days 15 and 20 then 5 and 10 with round",
                "active": True,
                "sequential_lines": True,
                "line_ids": [
                    fields.Command.create(
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "amount_round": 1,
                            "nb_days": 10,
                            "payment_days": "15,20",
                        },
                    ),
                    fields.Command.create(
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "nb_days": 10,
                            "payment_days": "10-5",
                        },
                    ),
                ],
            }
        )
        cls.amount_untaxed_lines = cls.payment_term_model.create(
            {
                "name": "10 percent + 40 percent + Balance",
                "active": True,
                "sequential_lines": True,
                "line_ids": [
                    fields.Command.create(
                        {
                            "value": "percent_amount_untaxed",
                            "value_amount": 10.0,
                        },
                    ),
                    fields.Command.create(
                        {
                            "value": "percent_amount_untaxed",
                            "value_amount": 40.0,
                            "nb_days": 1,
                        },
                    ),
                    fields.Command.create(
                        {"value": "percent", "value_amount": 100.0, "nb_days": 1},
                    ),
                ],
            }
        )
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Test tax",
                "amount_type": "percent",
                "amount": 10,
                "type_tax_use": "purchase",
            }
        )

    def _create_invoice(
        self, payment_term, date, quantity, price_unit, move_type="in_invoice"
    ):
        invoice_form = Form(
            self.invoice_model.with_context(default_move_type=move_type)
        )
        invoice_form.partner_id = self.partner
        invoice_form.invoice_payment_term_id = payment_term
        invoice_form.invoice_date = date
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.quantity = quantity
            line_form.price_unit = price_unit
            line_form.tax_ids.clear()
        invoice = invoice_form.save()
        return invoice

    def test_amount_untaxed_payment_term_error(self):
        vals = {
            "name": "10 percent + 40 percent + Balance",
            "sequential_lines": True,
            "line_ids": [
                fields.Command.create(
                    {
                        "value": "percent_amount_untaxed",
                        "value_amount": 110,
                    }
                )
            ],
        }
        with self.assertRaises(ValidationError):
            self.payment_term_model.create(vals)

    def test_invoice_amount_untaxed_payment_term(self):
        invoice = self._create_invoice(self.amount_untaxed_lines, "2020-01-01", 10, 100)
        with Form(invoice) as invoice_form:
            with invoice_form.invoice_line_ids.edit(0) as line_form:
                line_form.tax_ids.add(self.tax)
        invoice.action_post()
        self.assertEqual(invoice.line_ids[1].credit, 100.0)
        self.assertEqual(invoice.line_ids[2].credit, 400.0)
        self.assertEqual(invoice.line_ids[3].credit, 600.0)

    def test_out_invoice_amount_untaxed_payment_term(self):
        invoice = self._create_invoice(
            self.amount_untaxed_lines, "2020-01-01", 10, 100, move_type="out_invoice"
        )
        with Form(invoice) as invoice_form:
            with invoice_form.invoice_line_ids.edit(0) as line_form:
                line_form.tax_ids.add(self.tax)
        invoice.action_post()
        self.assertEqual(invoice.line_ids[1].debit, 100.0)
        self.assertEqual(invoice.line_ids[2].debit, 400.0)
        self.assertEqual(invoice.line_ids[3].debit, 600.0)

    def test_invoice_normal_payment_term(self):
        invoice = self._create_invoice(self.payment_term_0_day_5, "2020-01-01", 10, 100)
        invoice.action_post()
        for line in invoice.line_ids:
            if line.date_maturity:
                self.assertEqual(
                    fields.Date.to_string(line.date_maturity),
                    "2020-02-05",
                    "Incorrect due date for invoice with normal payment day on 5",
                )

    def test_invoice_multi_payment_term_day_1(self):
        invoice = self._create_invoice(
            self.payment_term_0_days_5_10, "2020-01-01", 10, 100
        )
        invoice.action_post()
        for line in invoice.line_ids:
            if line.date_maturity:
                self.assertEqual(
                    fields.Date.to_string(line.date_maturity),
                    "2020-01-05",
                    "Incorrect due date for invoice with payment days on 5 and 10 (1)",
                )

    def test_invoice_multi_payment_term_day_6(self):
        invoice = self._create_invoice(
            self.payment_term_0_days_5_10, "2020-01-06", 10, 100
        )
        invoice.action_post()
        for line in invoice.line_ids:
            if line.date_maturity:
                self.assertEqual(
                    fields.Date.to_string(line.date_maturity),
                    "2020-01-10",
                    "Incorrect due date for invoice with payment days on 5 and 10 (2)",
                )

    def test_invoice_multi_payment_term_sequential_day_1(self):
        invoice = self._create_invoice(
            self.payment_term_0_days_15_20_then_5_10, "2020-01-01", 10, 100
        )
        invoice.action_post()
        dates_maturity = []
        for line in invoice.line_ids:
            if line.date_maturity:
                dates_maturity.append(line.date_maturity)
        dates_maturity.sort()
        self.assertEqual(
            fields.Date.to_string(dates_maturity[0]),
            "2020-01-15",
            "Incorrect due date for invoice with payment days on "
            "15 and 20 then 5 and 10 (1)",
        )
        self.assertEqual(
            fields.Date.to_string(dates_maturity[1]),
            "2020-02-05",
            "Incorrect due date for invoice with payment days on "
            "15 and 20 then 5 and 10 (1)",
        )

    def test_invoice_multi_payment_term_sequential_day_18(self):
        invoice = self._create_invoice(
            self.payment_term_0_days_15_20_then_5_10, "2020-01-18", 10, 100
        )
        invoice.action_post()
        dates_maturity = []
        for line in invoice.line_ids:
            if line.date_maturity:
                dates_maturity.append(line.date_maturity)
        dates_maturity.sort()
        self.assertEqual(
            fields.Date.to_string(dates_maturity[0]),
            "2020-01-20",
            "Incorrect due date for invoice with payment days on "
            "15 and 20 then 5 and 10 (2)",
        )
        self.assertEqual(
            fields.Date.to_string(dates_maturity[1]),
            "2020-02-05",
            "Incorrect due date for invoice with payment days on "
            "15 and 20 then 5 and 10 (2)",
        )

    def test_invoice_multi_payment_term_sequential_day_25(self):
        invoice = self._create_invoice(
            self.payment_term_0_days_15_20_then_5_10, "2020-01-25", 10, 100
        )
        invoice.action_post()
        dates_maturity = []
        for line in invoice.line_ids:
            if line.date_maturity:
                dates_maturity.append(line.date_maturity)
        dates_maturity.sort()
        self.assertEqual(
            fields.Date.to_string(dates_maturity[0]),
            "2020-02-15",
            "Incorrect due date for invoice with payment days on "
            "15 and 20 then 5 and 10 (3)",
        )
        self.assertEqual(
            fields.Date.to_string(dates_maturity[1]),
            "2020-03-05",
            "Incorrect due date for invoice with payment days on "
            "15 and 20 then 5 and 10 (3)",
        )

    def test_invoice_multi_payment_term_round(self):
        invoice = self._create_invoice(
            self.payment_term_round, "2020-01-25", 10, 100.01
        )
        invoice.action_post()
        amounts = []
        for line in invoice.line_ids:
            if line.date_maturity:
                amounts.append(line.credit)
        self.assertEqual(
            amounts[0],
            500,
            "Incorrect round for invoice with payment days on "
            "15 and 20 then 5 and 10 (round)",
        )

    def test_decode_payment_days(self):
        expected_days = [5, 10]
        model = self.env["account.payment.term.line"]
        self.assertEqual(expected_days, model._decode_payment_days("5,10"))
        self.assertEqual(expected_days, model._decode_payment_days("5-10"))
        self.assertEqual(expected_days, model._decode_payment_days("5 10"))
        self.assertEqual(expected_days, model._decode_payment_days("10,5"))
        self.assertEqual(expected_days, model._decode_payment_days("10-5"))
        self.assertEqual(expected_days, model._decode_payment_days("10 5"))
        self.assertEqual(expected_days, model._decode_payment_days("5, 10"))
        self.assertEqual(expected_days, model._decode_payment_days("5 - 10"))
        self.assertEqual(expected_days, model._decode_payment_days("5    10"))
