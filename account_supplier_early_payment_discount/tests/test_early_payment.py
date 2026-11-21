# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date, timedelta

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestEarlyPayment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.buyer = cls.env["res.users"].create(
            {"name": "Buyer", "login": "early_payment_buyer"}
        )
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Early Payer Supplier",
                "buyer_id": cls.buyer.id,
                "early_payment_percent": 2.0,
                "early_payment_percent_2": 1.0,
                "early_payment_days": 10,
                "early_payment_base": "invoice",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Bolt", "type": "consu", "is_storable": True}
        )
        cls.product.supplier_taxes_id = False
        cls.group = cls.env.ref(
            "account_supplier_early_payment_discount.account_move_group_early_payment_credit_note"
        )
        cls.team = cls.env.ref(
            "account_supplier_early_payment_discount.mail_activity_team_early_payment_credit_note"
        )

    def _bill(self, partner=None, invoice_date="2026-09-10", post=True):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": (partner or self.supplier).id,
                "invoice_date": invoice_date,
                "invoice_date_due": invoice_date,
                "ref": f"SUP-{invoice_date}",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 10,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        if post:
            bill.action_post()
        return bill

    def test_the_two_discounts_chain(self):
        self.assertAlmostEqual(self.supplier._early_payment_ratio(), 0.0298)
        bill = self._bill()
        self.assertEqual(bill.early_payment_date, date(2026, 9, 20))
        self.assertAlmostEqual(bill.early_payment_amount, 29.8)

    def test_a_supplier_without_terms_has_no_early_payment(self):
        other = self.env["res.partner"].create({"name": "Plain Supplier"})
        bill = self._bill(partner=other)
        self.assertFalse(bill.early_payment_date)
        self.assertEqual(bill.early_payment_amount, 0.0)

    def test_the_days_count_from_the_receipt_when_the_supplier_says_so(self):
        self.supplier.early_payment_base = "receipt"
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.supplier.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_qty": 5,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        order.button_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 5
        picking.button_validate()
        received = date(2026, 9, 1)
        picking.date_done = received
        order.action_create_invoice()
        bill = order.invoice_ids
        bill.invoice_date = "2026-09-15"
        self.assertEqual(
            bill.early_payment_date,
            received + timedelta(days=10),
            "counted from the receipt",
        )

    def test_the_pay_date_is_the_business_day_before_a_weekend(self):
        """September 26th 2026 is a Saturday, the 30th a Wednesday."""
        self.assertEqual(
            self._bill(invoice_date="2026-09-16")._early_payment_pay_date(),
            date(2026, 9, 25),
        )
        self.assertEqual(
            self._bill(invoice_date="2026-09-20")._early_payment_pay_date(),
            date(2026, 9, 30),
        )

    def test_applying_the_discount_posts_a_credit_note_and_chases_the_supplier(self):
        self.group.user_ids = self.env.ref("base.user_admin")
        bill = self._bill()
        credit_note = bill.action_apply_early_payment()
        self.assertEqual(credit_note.move_type, "in_refund")
        self.assertEqual(credit_note.state, "posted")
        self.assertAlmostEqual(credit_note.amount_total, 29.8)
        self.assertEqual(credit_note.reversed_entry_id, bill)
        self.assertAlmostEqual(
            bill.amount_residual,
            970.2,
            msg="what is left to pay is the discounted amount",
        )
        self.assertEqual(bill.early_payment_credit_note_id, credit_note)
        activity = credit_note.activity_ids
        self.assertEqual(activity.team_id, self.team, "the team chases it, as a whole")
        self.assertFalse(activity.user_id)
        self.assertIn(self.env.ref("base.user_admin"), self.team.member_ids)
        self.assertIn(bill.name, activity.note)
        with self.assertRaises(UserError, msg="taken once"):
            bill.action_apply_early_payment()

    def test_without_anyone_in_the_group_the_buyer_chases_the_credit_note(self):
        self.group.user_ids = False
        credit_note = self._bill().action_apply_early_payment()
        self.assertEqual(credit_note.activity_ids.user_id, self.buyer)
        self.assertFalse(credit_note.activity_ids.team_id)

    def test_the_discount_needs_a_posted_bill_with_terms(self):
        with self.assertRaises(UserError):
            self._bill(post=False).action_apply_early_payment()
        plain = self.env["res.partner"].create({"name": "Plain Supplier"})
        with self.assertRaises(UserError):
            self._bill(partner=plain).action_apply_early_payment()
