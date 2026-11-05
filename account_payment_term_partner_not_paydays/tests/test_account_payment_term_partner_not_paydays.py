# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import new_test_user, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentTermPartnerNotPaydays(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.product = cls.env["product.product"].create({"name": "Product Test"})
        cls.billing_user = new_test_user(
            cls.env, login="billing_user", groups="account.group_account_invoice"
        )
        cls.readonly_user = new_test_user(
            cls.env, login="readonly_user", groups="account.group_account_readonly"
        )
        cls.payment_term_two_instalments = cls.env["account.payment.term"].create(
            {
                "name": "Half at 10 days, half at 30 days",
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 50, "nb_days": 10}
                    ),
                    Command.create(
                        {"value": "percent", "value_amount": 50, "nb_days": 30}
                    ),
                ],
            }
        )

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
        payment_term = values.get(
            "payment_term", self.env.ref("account.account_payment_term_30days")
        )
        create_values = {
            "partner_id": partner_id.id,
            "company_id": self.company.id,
            "invoice_date": values.get("invoice_date", "2025-07-15"),
            "move_type": values.get("move_type", "out_invoice"),
            "invoice_payment_term_id": payment_term.id,
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
                                "price_unit": 100,
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

    def test_billing_user_reads_days_not_pay(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner()
        self.env.invalidate_all()
        self.assertTrue(partner.with_user(self.billing_user).days_not_pay)

    def test_billing_user_sees_range_warning(self):
        self.enable_config_days_not_pay()
        invoice = self.create_invoice(add_lines=True)
        self.env.invalidate_all()
        invoice = invoice.with_user(self.billing_user)
        self.assertEqual(len(invoice.partner_id.partner_not_pay_ids), 1)
        self.assertIn("01/08/2025", invoice.message_range_not_pay)

    def test_readonly_user_reads_partner_ranges(self):
        partner = self.create_partner()
        self.env.invalidate_all()
        self.assertEqual(
            partner.with_user(self.readonly_user).partner_not_pay_ids.date_start,
            date(2025, 8, 1),
        )

    def test_billing_user_cannot_change_ranges(self):
        partner = self.create_partner()
        with self.assertRaises(AccessError):
            partner.partner_not_pay_ids.with_user(self.billing_user).write(
                {"date_end": "2025-08-20"}
            )

    def test_action_post_moves_payment_term_lines_in_range(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            customer_payment_days=False,
            ranges=[{"date_start": "2025-08-10", "date_end": "2025-08-20"}],
        )
        invoice = self.create_invoice(
            partner=partner,
            payment_term=self.payment_term_two_instalments,
            invoice_date_due=False,
            add_lines=True,
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 8, 14))
        invoice.with_user(self.billing_user).action_post()
        term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(
            sorted(term_lines.mapped("date_maturity")),
            [date(2025, 7, 25), date(2025, 9, 14)],
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 9, 14))

    def test_action_post_keeps_payment_term_lines_out_of_range(self):
        """Moving the last instalment must not drag an earlier one that was
        valid into another non-payment range."""
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            ranges=[{"date_start": "2025-10-01", "date_end": "2025-11-30"}]
        )
        invoice = self.create_invoice(
            partner=partner,
            payment_term=self.payment_term_two_instalments,
            invoice_date="2025-09-05",
            invoice_date_due=False,
            add_lines=True,
        )
        invoice.with_user(self.billing_user).action_post()
        term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(
            sorted(term_lines.mapped("date_maturity")),
            [date(2025, 9, 17), date(2025, 12, 5)],
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 12, 5))

    def test_action_post_moves_earlier_payment_term_line_in_range(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            customer_payment_days=False,
            ranges=[{"date_start": "2025-07-20", "date_end": "2025-07-31"}],
        )
        invoice = self.create_invoice(
            partner=partner,
            payment_term=self.payment_term_two_instalments,
            invoice_date_due=False,
            add_lines=True,
        )
        invoice.with_user(self.billing_user).action_post()
        term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(
            sorted(term_lines.mapped("date_maturity")),
            [date(2025, 8, 14), date(2025, 8, 25)],
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 8, 25))

    def test_post_from_list_moves_due_date(self):
        self.enable_config_days_not_pay()
        invoices = self.create_invoice(add_lines=True) | self.create_invoice(
            add_lines=True
        )
        wizard = (
            self.env["validate.account.move"]
            .with_user(self.billing_user)
            .with_context(active_model="account.move", active_ids=invoices.ids)
            .create({})
        )
        wizard.validate_move()
        self.assertEqual(invoices.mapped("invoice_date_due"), [date(2025, 9, 17)] * 2)

    def test_action_post_without_payment_term_moves_its_line(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(customer_payment_days=False)
        invoice = self.create_invoice(
            partner=partner,
            payment_term=self.env["account.payment.term"],
            add_lines=True,
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 8, 15))
        invoice.with_user(self.billing_user).action_post()
        term_line = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(term_line.date_maturity, date(2025, 9, 15))
        self.assertEqual(invoice.invoice_date_due, date(2025, 9, 15))

    def test_action_post_no_payment_day_after_due_day(self):
        """With payment days 5 and 17 and a due date on the 19th, none of the
        payment days comes later in the month, so the first one of the next
        month is taken instead of keeping the 19th."""
        self.enable_config_days_not_pay()
        invoice = self.create_invoice(
            payment_term=self.env["account.payment.term"],
            invoice_date="2025-07-20",
            invoice_date_due="2025-08-19",
            add_lines=True,
        )
        invoice.with_user(self.billing_user).action_post()
        self.assertEqual(invoice.invoice_date_due, date(2025, 9, 5))

    def test_action_post_range_ending_before_month_end(self):
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            ranges=[{"date_start": "2025-08-01", "date_end": "2025-08-10"}]
        )
        invoice = self.create_invoice(
            partner=partner,
            invoice_date="2025-07-05",
            invoice_date_due=False,
            add_lines=True,
        )
        self.assertEqual(invoice.invoice_date_due, date(2025, 8, 5))
        invoice.with_user(self.billing_user).action_post()
        self.assertEqual(invoice.invoice_date_due, date(2025, 8, 17))

    def test_action_post_due_date_on_valid_payment_day(self):
        """Whatever the invoice date, the posted due date is one of the
        partner's payment days, outside every non-payment range, and never
        earlier than the due date computed from the payment term."""
        self.enable_config_days_not_pay()
        partner = self.create_partner(
            ranges=[
                {"date_start": "2025-08-01", "date_end": "2025-08-20"},
                {"date_start": "2025-09-15", "date_end": "2025-09-30"},
            ]
        )
        for day in range(1, 32):
            invoice = self.create_invoice(
                partner=partner,
                invoice_date=date(2025, 7, day),
                invoice_date_due=False,
                add_lines=True,
            )
            due_before = invoice.invoice_date_due
            invoice.with_user(self.billing_user).action_post()
            due_after = invoice.invoice_date_due
            self.assertIn(due_after.day, (5, 17), invoice.invoice_date)
            self.assertGreaterEqual(due_after, due_before, invoice.invoice_date)
            self.assertFalse(
                partner._check_partner_range_not_pay(
                    compare_date=due_after, move_type="out_invoice"
                ),
                invoice.invoice_date,
            )

    def test_range_change_updates_warning(self):
        self.enable_config_days_not_pay()
        invoice = self.create_invoice(add_lines=True)
        billing_invoice = invoice.with_user(self.billing_user)
        self.assertTrue(billing_invoice.message_range_not_pay)
        invoice.partner_id.partner_not_pay_ids.write(
            {"date_start": "2025-10-01", "date_end": "2025-10-31"}
        )
        self.assertFalse(billing_invoice.message_range_not_pay)

    def test_disabling_setting_hides_warning(self):
        self.enable_config_days_not_pay()
        invoice = self.create_invoice(add_lines=True)
        billing_invoice = invoice.with_user(self.billing_user)
        self.assertTrue(billing_invoice.message_range_not_pay)
        self.env["res.config.settings"].create({"days_not_pay": False}).execute()
        self.assertFalse(billing_invoice.message_range_not_pay)

    def test_enabling_setting_shows_warning(self):
        self.env["res.config.settings"].create({"days_not_pay": False}).execute()
        invoice = self.create_invoice(add_lines=True)
        billing_invoice = invoice.with_user(self.billing_user)
        self.assertFalse(billing_invoice.message_range_not_pay)
        self.enable_config_days_not_pay()
        self.assertTrue(billing_invoice.message_range_not_pay)

    def test_ranges_of_different_types_can_overlap(self):
        partner = self.create_partner(
            ranges=[
                {"date_start": "2025-08-01", "date_end": "2025-08-31"},
                {
                    "date_start": "2025-08-01",
                    "date_end": "2025-08-31",
                    "type": "in_invoice",
                },
            ]
        )
        self.assertEqual(len(partner.partner_not_pay_ids), 2)

    def test_range_types_exclude_journal_entries(self):
        types = dict(
            self.env["res.partner.not.pay"]
            ._fields["type"]
            ._description_selection(self.env)
        )
        self.assertNotIn("entry", types)

    def test_warning_message_separates_sentences(self):
        self.enable_config_days_not_pay()
        invoice = self.create_invoice(add_lines=True)
        self.assertIn("of not pay to the partner. If", invoice.message_range_not_pay)
