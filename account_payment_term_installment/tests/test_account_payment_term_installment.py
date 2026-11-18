# Copyright 2026 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestAccountPaymentTermInstallment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.term = cls.env["account.payment.term"].create({"name": "Test Term"})

    def test_default_values(self):
        self.assertEqual(self.term.installment_count, 1)
        self.assertEqual(self.term.installment_interval_days, 30)

    def test_generate_single_installment_keeps_balance(self):
        self.term.installment_count = 1
        self.term._generate_installment_lines()
        self.assertEqual(len(self.term.line_ids), 1)
        self.assertEqual(self.term.line_ids[0].value, "balance")
        self.assertEqual(self.term.line_ids[0].days, 0)

    def test_generate_three_installments(self):
        self.term.installment_count = 3
        self.term.installment_interval_days = 30
        self.term._generate_installment_lines()
        lines = self.term.line_ids.sorted("days")
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0].value, "percent")
        self.assertAlmostEqual(lines[0].value_amount, 100.0 / 3, places=4)
        self.assertEqual(lines[0].days, 30)
        self.assertEqual(lines[1].value, "percent")
        self.assertEqual(lines[1].days, 60)
        self.assertEqual(lines[2].value, "balance")
        self.assertEqual(lines[2].days, 90)

    def test_generate_custom_interval(self):
        self.term.installment_count = 2
        self.term.installment_interval_days = 15
        self.term._generate_installment_lines()
        lines = self.term.line_ids.sorted("days")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].days, 15)
        self.assertEqual(lines[1].days, 30)

    def test_onchange_regenerates_lines(self):
        form = Form(self.env["account.payment.term"])
        form.name = "Onchange Term"
        form.installment_count = 4
        form.installment_interval_days = 10
        term = form.save()
        lines = term.line_ids.sorted("days")
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[-1].value, "balance")
        self.assertEqual(lines[-1].days, 40)

    def test_constrains_count_below_one(self):
        with self.assertRaises(ValidationError):
            self.term.installment_count = 0

    def test_constrains_interval_negative(self):
        with self.assertRaises(ValidationError):
            self.term.installment_interval_days = -5
