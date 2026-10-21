# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentTermPartnerNotPaydays(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.product = cls.env["product.product"].create({"name": "Product Test"})

    def enable_config_days_not_pay(self):
        conf = self.env["res.config.settings"].create({"days_not_pay": True})
        conf.execute()

    def create_partner(self, **values):
        range_not_pay_days = [
            Command.create(range_values)
            for range_values in values.get(
                "ranges", [{"date_start": "2025-08-01", "date_end": "2025-08-31"}]
            )
        ]
        create_values = {
            "name": "Partner Test",
            "customer_payment_days": values.get("customer_payment_days", "5,17"),
            "supplier_payment_days": values.get("supplier_payment_days", False),
        }
        if values.get("failed_range", False):
            range_not_pay_days.append(
                Command.create({"date_start": "2025-08-06", "date_end": "2025-08-23"})
            )
        create_values.update({"partner_not_pay_ids": range_not_pay_days})
        return self.env["res.partner"].create(create_values)

    def create_invoice(self, **values):
        partner_id = values.get("partner") or self.create_partner()
        create_values = {
            "partner_id": partner_id.id,
            "company_id": self.company.id,
            "invoice_date": values.get("invoice_date", "2025-07-15"),
            "move_type": values.get("move_type", "out_invoice"),
            "invoice_payment_term_id": self.env.ref(
                "account.account_payment_term_30days"
            ).id,
        }
        if values.get("invoice_date_due", "2025-08-15"):
            create_values["invoice_date_due"] = values.get(
                "invoice_date_due", "2025-08-15"
            )
        if values.get("add_lines", False):
            create_values.update(
                {
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "Test",
                                "product_id": self.product.id,
                                "debit": 100,
                                "credit": 0,
                            }
                        )
                    ]
                }
            )

        return self.env["account.move"].create(create_values)

    def test_overlap_days_not_pay(self):
        self.enable_config_days_not_pay()
        invoice = self.create_invoice()
        self.assertTrue(invoice.message_range_not_pay)
        self.assertIn("01/08/2025", invoice.message_range_not_pay)
        self.assertIn("31/08/2025", invoice.message_range_not_pay)
        invoice_entry = self.create_invoice(
            **{
                "move_type": "entry",
            }
        )
        self.assertFalse(invoice_entry.message_range_not_pay)

    def test_action_post(self):
        self.enable_config_days_not_pay()
        invoice = self.create_invoice(
            **{
                "add_lines": True,
            }
        )
        invoice.action_post()
        self.assertEqual(invoice.invoice_date_due, date(2025, 9, 17))

    def test_check_date_start_end(self):
        with self.assertRaises(ValidationError):
            self.create_partner(
                **{
                    "failed_range": True,
                }
            )

    def test_days_not_pay_disabled(self):
        self.env["ir.config_parameter"].set_param(
            "account_payment_term_partner_not_paydays.days_not_pay", False
        )
        invoice = self.create_invoice()
        self.assertFalse(invoice.message_range_not_pay)

    def test_action_post_range_over_several_months(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            ranges=[{"date_start": "2025-08-01", "date_end": "2025-09-30"}]
        )
        invoice = self.create_invoice(partner=partner, add_lines=True)
        invoice.action_post()
        self.assertEqual(invoice.invoice_date_due, date(2025, 10, 17))

    def test_action_post_without_partner_payment_days(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(customer_payment_days=False)
        invoice = self.create_invoice(partner=partner, add_lines=True)
        self.assertFalse(invoice.get_pay_days())
        invoice.action_post()
        self.assertEqual(invoice.invoice_date_due, date(2025, 9, 14))

    def test_action_post_vendor_bill(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            customer_payment_days=False,
            supplier_payment_days="10",
            ranges=[
                {
                    "date_start": "2025-08-01",
                    "date_end": "2025-08-31",
                    "type": "in_invoice",
                }
            ],
        )
        bill = self.create_invoice(
            partner=partner,
            move_type="in_invoice",
            invoice_date="2025-07-05",
            add_lines=True,
        )
        self.assertTrue(bill.message_range_not_pay)
        bill.action_post()
        self.assertEqual(bill.invoice_date_due, date(2025, 9, 10))

    def test_next_with_day_without_pay_day(self):
        move = self.env["account.move"]
        self.assertEqual(move.next_with_day(date(2025, 9, 14), 0), date(2025, 9, 14))
        self.assertEqual(move.next_with_day(date(2025, 9, 14), 17), date(2025, 9, 17))

    def test_check_date_start_after_date_end(self):
        with self.assertRaises(ValidationError):
            self.create_partner(
                ranges=[{"date_start": "2025-08-31", "date_end": "2025-08-01"}]
            )

    def test_due_date_applies_partner_payment_days(self):
        partner = self.create_partner(
            customer_payment_days="20",
            ranges=[{"date_start": "2025-10-01", "date_end": "2025-10-31"}],
        )
        invoice = self.create_invoice(
            partner=partner, invoice_date_due=False, add_lines=True
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 8, 20))

    def test_next_with_day_after_end_of_month(self):
        move = self.env["account.move"]
        self.assertEqual(move.next_with_day(date(2025, 2, 10), 31), date(2025, 2, 28))
        self.assertEqual(move.next_with_day(date(2024, 2, 10), 30), date(2024, 2, 29))
        self.assertEqual(move.next_with_day(date(2025, 4, 10), 31), date(2025, 4, 30))

    def test_action_post_pay_day_after_end_of_month(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            customer_payment_days="31",
            ranges=[{"date_start": "2025-01-15", "date_end": "2025-02-10"}],
        )
        invoice = self.create_invoice(
            partner=partner,
            invoice_date="2025-01-01",
            invoice_date_due=False,
            add_lines=True,
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 1, 31))
        self.assertTrue(invoice.message_range_not_pay)
        invoice.action_post()
        self.assertEqual(invoice.invoice_date_due, date(2025, 2, 28))
