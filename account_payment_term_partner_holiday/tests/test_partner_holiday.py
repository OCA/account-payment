# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import psycopg2

from odoo import fields
from odoo.tests import common
from odoo.tests.common import Form
from odoo.tools.misc import mute_logger


class TestPartnerHoliday(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_1 = self.env["res.partner"].create(
            {
                "name": "Partner test 1",
                "holiday_ids": [
                    (
                        0,
                        0,
                        {
                            "day_from": "1",
                            "month_from": "02",
                            "day_to": "31",
                            "month_to": "02",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "day_from": "1",
                            "month_from": "03",
                            "day_to": "1",
                            "month_to": "04",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "day_from": "12",
                            "month_from": "06",
                            "day_to": "13",
                            "month_to": "06",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "day_from": "15",
                            "month_from": "06",
                            "day_to": "16",
                            "month_to": "06",
                        },
                    ),
                ],
            }
        )
        self.partner_1_child = self.env["res.partner"].create(
            {"name": "Partner child", "parent_id": self.partner_1.id, "type": "invoice"}
        )
        self.partner_2 = self.env["res.partner"].create({"name": "Partner test 2"})
        self.payment_term_immediate = self.env["account.payment.term"].create(
            {
                "name": "Immediate",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                        },
                    )
                ],
            }
        )
        self.payment_term_10_days = self.env["account.payment.term"].create(
            {
                "name": "10 Days",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 10,
                        },
                    )
                ],
            }
        )
        self.payment_term_with_holidays = self.env["account.payment.term"].create(
            {
                "name": "Immediate (with holidays)",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                        },
                    )
                ],
                "holiday_ids": [
                    (0, 0, {"holiday": "2021-06-14", "date_postponed": "2021-07-08"})
                ],
            }
        )
        self.payment_term_immediate_custom = self.env["account.payment.term"].create(
            {
                "name": "Immediate (with custom payment days)",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                            "payment_days": "5,10",
                        },
                    )
                ],
            }
        )
        self.journal = self.env["account.journal"].create(
            {"name": "Test sale", "type": "sale", "code": "TEST-SALE"}
        )
        self.product = self.env["product.product"].create(
            {"name": "Test product", "type": "service"}
        )
        self.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        self.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "ACC",
                "account_type": "income_other",
                "reconcile": True,
            }
        )

    def test_check_partner_holiday_constraint(self):
        vals = {
            "partner_id": self.partner_2.id,
            "day_from": "1",
            "month_from": "12",
            "day_to": "1",
            "month_to": "01",
        }
        with self.assertRaises(psycopg2.IntegrityError), mute_logger("odoo.sql_db"):
            self.env["res.partner.holiday"].create(vals)

    def test_check_dates_in_partner_1(self):
        self.assertEqual(
            self.partner_1.is_date_in_holiday(fields.Date.from_string("2021-02-01")),
            [
                fields.Date.from_string("2021-02-01"),
                fields.Date.from_string("2021-02-28"),
            ],
        )
        self.assertEqual(
            self.partner_1.is_date_in_holiday(fields.Date.from_string("2021-03-01")),
            [
                fields.Date.from_string("2021-03-01"),
                fields.Date.from_string("2021-04-01"),
            ],
        )
        self.assertFalse(
            self.partner_1.is_date_in_holiday(fields.Date.from_string("2021-04-02"))
        )

    def test_check_dates_in_partner_1_only_february(self):
        self.assertEqual(len(self.partner_1.holiday_ids), 4)
        self.partner_1.holiday_ids.filtered(lambda x: x.month_from == "03").unlink()
        self.assertEqual(len(self.partner_1.holiday_ids), 3)
        self.assertEqual(
            self.partner_1.is_date_in_holiday(fields.Date.from_string("2021-02-01")),
            [
                fields.Date.from_string("2021-02-01"),
                fields.Date.from_string("2021-02-28"),
            ],
        )
        self.assertFalse(
            self.partner_1.is_date_in_holiday(fields.Date.from_string("2021-03-01"))
        )

    def test_check_dates_in_partner_2(self):
        self.assertFalse(
            self.partner_2.is_date_in_holiday(fields.Date.from_string("2021-02-01"))
        )
        self.assertFalse(
            self.partner_2.is_date_in_holiday(fields.Date.from_string("2021-02-01"))
        )
        self.assertFalse(
            self.partner_2.is_date_in_holiday(fields.Date.from_string("2021-02-10"))
        )
        self.assertFalse(
            self.partner_2.is_date_in_holiday(fields.Date.from_string("2021-04-02"))
        )

    def _set_invoice_form(self, partner_id, date):
        move_form = Form(
            self.env["account.move"].with_context(
                default_journal_id=self.journal.id,
                default_partner_id=partner_id,
                default_move_type="out_invoice",
                default_invoice_date=date,
            ),
        )
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
        return move_form

    def test_invoice_payment_term_partner_1(self):
        invoice_form = self._set_invoice_form(self.partner_1.id, "2021-02-01")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-04-02")
        )
        invoice_form.invoice_payment_term_id = self.payment_term_10_days
        with invoice_form.invoice_line_ids.new() as line:
            line.product_id = self.product
        invoice = invoice_form.save()
        self.assertEqual(
            invoice.invoice_date_due, fields.Date.from_string("2021-04-02")
        )
        # Set to 2021-04-01
        invoice_form = self._set_invoice_form(self.partner_1.id, "2021-04-01")
        invoice_form.invoice_payment_term_id = self.payment_term_10_days
        with invoice_form.invoice_line_ids.new() as line:
            line.product_id = self.product
        invoice = invoice_form.save()
        self.assertEqual(
            invoice.invoice_date_due, fields.Date.from_string("2021-04-11")
        )

    def test_invoice_payment_term_custom_partner_1(self):
        invoice_form = self._set_invoice_form(self.partner_1.id, "2021-06-12")
        invoice_form.invoice_payment_term_id = self.payment_term_with_holidays
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-07-08")
        )
        invoice_form = self._set_invoice_form(self.partner_1.id, "2021-02-01")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate_custom
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-04-05")
        )

    def test_invoice_payment_term_partner_1_child(self):
        invoice_form = self._set_invoice_form(self.partner_1_child.id, "2021-02-01")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-04-02")
        )
        invoice_form.invoice_payment_term_id = self.payment_term_10_days
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-04-02")
        )
        # Set to 2021-04-01
        invoice_form = self._set_invoice_form(self.partner_1_child.id, "2021-04-01")
        invoice_form.invoice_payment_term_id = self.payment_term_10_days
        with invoice_form.invoice_line_ids.new() as line:
            line.product_id = self.product
        invoice = invoice_form.save()
        self.assertEqual(
            invoice.invoice_date_due, fields.Date.from_string("2021-04-11")
        )

    def test_invoice_payment_term_custom_partner_1_child(self):
        invoice_form = self._set_invoice_form(self.partner_1_child.id, "2021-06-12")
        invoice_form.invoice_payment_term_id = self.payment_term_with_holidays
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-07-08")
        )
        invoice_form = self._set_invoice_form(self.partner_1_child.id, "2021-02-01")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate_custom
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-04-05")
        )

    def test_invoice_payment_term_partner_2(self):
        invoice_form = self._set_invoice_form(self.partner_2.id, "2021-02-01")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-02-01")
        )
        invoice_form.invoice_payment_term_id = self.payment_term_10_days
        with invoice_form.invoice_line_ids.new() as line:
            line.product_id = self.product
        invoice = invoice_form.save()
        self.assertEqual(
            invoice.invoice_date_due, fields.Date.from_string("2021-02-11")
        )

    def test_invoice_payment_term_custom_partner_2(self):
        invoice_form = self._set_invoice_form(self.partner_2.id, "2021-06-12")
        invoice_form.invoice_payment_term_id = self.payment_term_with_holidays
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-06-12")
        )
        invoice_form = self._set_invoice_form(self.partner_2.id, "2021-06-14")
        invoice_form.invoice_payment_term_id = self.payment_term_with_holidays
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-07-08")
        )
        invoice_form = self._set_invoice_form(self.partner_2.id, "2021-02-01")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate_custom
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-02-05")
        )

    def test_partner_1_invoice_date_june_13(self):
        invoice_form = self._set_invoice_form(self.partner_1.id, "2021-06-13")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-06-14")
        )

    def test_partner_2_invoice_change_due_date_on_confirm(self):
        """A partner's holidays could have changed since we created the invoice. Let's
        ensure that the due dates are correct when we post it"""
        invoice_form = self._set_invoice_form(self.partner_2.id, "2021-06-13")
        invoice_form.invoice_payment_term_id = self.payment_term_immediate
        self.assertEqual(
            invoice_form.invoice_date_due, fields.Date.from_string("2021-06-13")
        )
        invoice = invoice_form.save()
        self.partner_2.write(
            {
                "holiday_ids": [
                    (
                        0,
                        0,
                        {
                            "day_from": "1",
                            "month_from": "06",
                            "day_to": "31",
                            "month_to": "06",
                        },
                    ),
                ]
            }
        )
        self.assertEqual(
            invoice.invoice_date_due, fields.Date.from_string("2021-06-13")
        )
        invoice.action_post()
        self.assertEqual(
            invoice.invoice_date_due, fields.Date.from_string("2021-07-01")
        )

    def test_partner_1_get_valid_due_date(self):
        self.assertEqual(
            self.partner_1._get_valid_due_date(fields.Date.from_string("2021-01-01")),
            fields.Date.from_string("2021-01-01"),
        )
        self.assertEqual(
            self.partner_1._get_valid_due_date(fields.Date.from_string("2021-02-01")),
            fields.Date.from_string("2021-04-02"),
        )
        self.assertEqual(
            self.partner_1._get_valid_due_date(fields.Date.from_string("2021-06-12")),
            fields.Date.from_string("2021-06-14"),
        )
        self.assertEqual(
            self.partner_1._get_valid_due_date(fields.Date.from_string("2021-06-14")),
            fields.Date.from_string("2021-06-14"),
        )
