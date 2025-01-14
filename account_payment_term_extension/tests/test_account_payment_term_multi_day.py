import odoo.tests.common as common
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, tagged


@tagged("post_install", "-at_install")
class TestAccountPaymentTermMultiDay(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        if not cls.env.company.chart_template_id:
            # Load a CoA if there's none in current company
            coa = cls.env.ref("l10n_generic_coa.configurable_chart_template", False)
            if not coa:
                # Load the first available CoA
                coa = cls.env["account.chart.template"].search(
                    [("visible", "=", True)], limit=1
                )
            coa.try_loading(company=cls.env.company, install_demo=False)
        cls.payment_term_model = cls.env["account.payment.term"]
        cls.invoice_model = cls.env["account.move"]
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.foreign_partner = cls.env["res.partner"].create(
            {"name": "Test Foreign Partner", "country_id": cls.env.ref("base.es").id}
        )
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.foreign_currency = cls.env["res.currency"].search([("name", "=", "EUR")])
        cls.payment_term_0_day_5 = cls.payment_term_model.create(
            {
                "name": "Normal payment in day 5",
                "active": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 5,
                            "payment_days": "5",
                        },
                    )
                ],
            }
        )
        cls.payment_term_0_days_5_10 = cls.payment_term_model.create(
            {
                "name": "Payment for days 5 and 10",
                "active": True,
                "line_ids": [
                    (0, 0, {"value": "balance", "days": 0, "payment_days": "5,10"})
                ],
            }
        )
        cls.payment_term_0_days_15_20_then_5_10 = cls.payment_term_model.create(
            {
                "name": "Payment for days 15 and 20 then 5 and 10",
                "active": True,
                "sequential_lines": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "days": 0,
                            "payment_days": "15,20",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
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
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "amount_round": 1,
                            "days": 10,
                            "payment_days": "15,20",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 10,
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
                    (
                        0,
                        0,
                        {
                            "value": "percent_amount_untaxed",
                            "value_amount": 10.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "percent_amount_untaxed",
                            "value_amount": 40.0,
                            "days": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {"value": "balance", "days": 1},
                    ),
                ],
            }
        )
        cls.advance_60days = cls.payment_term_model.create(
            {
                "name": "30% Now, Balance 60 Days",
                "active": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 30.0,
                            "days": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "value_amount": 0.0,
                            "days": 60,
                        },
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
        self,
        payment_term,
        date,
        quantity,
        price_unit,
        move_type="in_invoice",
        foreing_partner=False,
    ):
        invoice_form = Form(
            self.invoice_model.with_context(default_move_type=move_type)
        )
        invoice_form.partner_id = (
            self.partner if not foreing_partner else self.foreign_partner
        )
        invoice_form.invoice_payment_term_id = payment_term
        invoice_form.invoice_date = date
        if foreing_partner:
            invoice_form.currency_id = self.foreign_currency
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.quantity = quantity
            line_form.price_unit = price_unit
            line_form.tax_ids.clear()
        invoice = invoice_form.save()
        return invoice

    def test_amount_untaxed_payment_term_error(self):
        payment_term_form = Form(self.payment_term_model)
        payment_term_form.name = "10 percent + 40 percent + Balance"
        payment_term_form.sequential_lines = True
        with payment_term_form.line_ids.new() as line_form:
            line_form.value = "percent_amount_untaxed"
            line_form.value_amount = 110
        with self.assertRaises(ValidationError):
            payment_term_form.save()

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
            amounts,
            [500.05, 500.05],
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

    def test_invoice_advance_60days_payment_term(self):
        invoice = self._create_invoice(
            self.advance_60days, fields.Date.today(), 1, 900, foreing_partner=True
        )
        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            invoice.currency_id,
            invoice.company_id.currency_id,
            invoice.company_id,
            invoice.date,
        )
        invoice.action_post()
        self.assertNotEqual(invoice.currency_id, invoice.company_id.currency_id)
        first_amount_original_currency = invoice.currency_id.round(
            invoice.amount_total * 0.3
        )
        second_amount_original_currency = invoice.currency_id.round(
            invoice.amount_total - first_amount_original_currency
        )
        expected_first_amount = invoice.currency_id.round(
            first_amount_original_currency * conversion_rate
        )
        expected_second_amount = invoice.currency_id.round(
            second_amount_original_currency * conversion_rate
        )
        self.assertEqual(invoice.line_ids[1].credit, expected_first_amount)
        self.assertEqual(invoice.line_ids[2].credit, expected_second_amount)
