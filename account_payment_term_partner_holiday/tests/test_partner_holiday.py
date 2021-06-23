# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.tests.common import Form
from odoo import fields


class TestPartnerHoliday(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_1 = self.env["res.partner"].create({
            "name": "Partner test 1",
            "holiday_ids": [(0, 0, {
                "day_from": "1",
                "month_from": "2",
                "day_to": "31",
                "month_to": "2",
            })]
        })
        self.partner_2 = self.env["res.partner"].create({"name": "Partner test 2"})
        self.payment_term_immediate = self.env["account.payment.term"].create({
            "name": "Immediate",
            "line_ids": [(0, 0, {
                "value": "balance",
                "days": 0,
                "option": "day_after_invoice_date"
            })]
        })
        self.payment_term_10_days = self.env["account.payment.term"].create({
            "name": "10 Days",
            "line_ids": [(0, 0, {
                "value": "balance",
                "days": 10,
                "option": "day_after_invoice_date"
            })]
        })
        self.journal = self.env["account.journal"].create({
            "name": "Test sale",
            "type": "sale",
            "code": "TEST-SALE"
        })
        self.product = self.env["product.product"].create({
            "name": "Test product",
            "type": "service"
        })

    def test_check_dates_in_partner_1(self):
        self.assertEqual(
            self.partner_1.is_date_in_holiday(fields.Date.from_string("2021-02-01")), [
                fields.Date.from_string("2021-02-01"),
                fields.Date.from_string("2021-02-28")
            ]
        )
        self.assertEqual(
            self.partner_1.is_date_in_holiday(fields.Date.from_string("2021-02-10")), [
                fields.Date.from_string("2021-02-01"),
                fields.Date.from_string("2021-02-28")
            ]
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
            self.partner_2.is_date_in_holiday(fields.Date.from_string("2021-03-01"))
        )

    def test_invoice_payment_term_partner_1(self):
        invoice_form = Form(
            self.env['account.invoice'].with_context(
                default_journal_id=self.journal.id,
                default_partner_id=self.partner_1.id,
                default_date_invoice="2021-02-01"
            ),
            view="account.invoice_form"
        )
        invoice_form.payment_term_id = self.payment_term_immediate
        self.assertEqual(invoice_form.date_due, fields.Date.from_string("2021-03-01"))
        invoice_form.payment_term_id = self.payment_term_10_days
        self.assertEqual(invoice_form.date_due, fields.Date.from_string("2021-03-01"))
        # Save invoice and check action_invoice_open function
        with invoice_form.invoice_line_ids.new() as line:
            line.product_id = self.product
        invoice = invoice_form.save()
        invoice.date_due = "2021-02-01"
        self.assertEqual(invoice.date_due, fields.Date.from_string("2021-02-01"))
        invoice.action_invoice_open()
        self.assertEqual(invoice.date_due, fields.Date.from_string("2021-03-01"))

    def test_invoice_payment_term_partner_2(self):
        invoice_form = Form(
            self.env['account.invoice'].with_context(
                default_journal_id=self.journal.id,
                default_partner_id=self.partner_2.id,
                default_date_invoice="2021-02-01"
            ),
            view="account.invoice_form"
        )
        invoice_form.payment_term_id = self.payment_term_immediate
        self.assertEqual(invoice_form.date_due, fields.Date.from_string("2021-02-01"))
        invoice_form.payment_term_id = self.payment_term_10_days
        self.assertEqual(invoice_form.date_due, fields.Date.from_string("2021-02-11"))
