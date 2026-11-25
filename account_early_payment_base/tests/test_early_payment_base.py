# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEarlyPaymentBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.resource_calendar_id = cls.env["resource.calendar"].create(
            {"name": "Monday to Friday", "company_id": cls.company.id}
        )
        cls.env["resource.calendar.leaves"].create(
            {
                "name": "Holiday",
                "calendar_id": cls.company.resource_calendar_id.id,
                "date_from": "2026-09-16 00:00:00",
                "date_to": "2026-09-16 23:59:59",
            }
        )

    def test_business_days_skip_weekends_and_holidays(self):
        # Friday the 11th: Mon 14, Tue 15, (16 off), Thu 17, Fri 18, Mon 21 ...
        self.assertEqual(
            self.company._add_business_days(date(2026, 9, 11), 3), date(2026, 9, 17)
        )
        self.assertEqual(
            self.company._add_business_days(date(2026, 9, 11), 8), date(2026, 9, 24)
        )
        self.assertTrue(self.company._is_business_day(date(2026, 9, 17)))
        self.assertFalse(self.company._is_business_day(date(2026, 9, 16)))
        self.assertFalse(self.company._is_business_day(date(2026, 9, 19)))

    def test_without_calendar_the_days_are_calendar_days(self):
        self.company.resource_calendar_id = False
        self.env["resource.calendar"].search([]).write(
            {"company_id": self.env["res.company"].create({"name": "Other"}).id}
        )
        self.assertEqual(
            self.company._add_business_days(date(2026, 9, 11), 8), date(2026, 9, 19)
        )

    def test_nothing_applies_on_its_own(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env["res.partner"].create({"name": "Customer"}).id,
                "invoice_date": "2026-09-11",
                "invoice_line_ids": [
                    Command.create({"name": "Line", "quantity": 1, "price_unit": 100.0})
                ],
            }
        )
        invoice.action_post()
        self.assertFalse(invoice.early_payment_date)
        self.assertEqual(invoice.early_payment_amount, 0.0)
        self.assertFalse(invoice.early_payment_can_apply)
        with self.assertRaises(UserError):
            invoice.action_apply_early_payment()
