# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.fields import Date

from .common import TestAccountCashDiscountPaymentCommon


class TestAccountCashDiscountPayment(TestAccountCashDiscountPaymentCommon):
    def test_invoice_payment_discount(self):
        invoice_date = Date.today()
        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 2000, 25, []
        )
        invoice.action_post()

        payment_order = self.PaymentOrder.create(
            {"payment_mode_id": self.payment_mode_out.id, "payment_type": "outbound"}
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "target_move": "posted",
                "journal_ids": [(6, 0, [self.purchase_journal.id])],
            }
        )
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        move_lines = payment_line_wizard.move_line_ids
        self.assertEqual(len(move_lines), 1)

        move_line = move_lines[0]
        self.assertAlmostEqual(move_line.discount_amount, 500, 2)

        payment_line_wizard.create_payment_lines()

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1500)

        # Change the amount of the line and trigger the onchange amount method
        # and verify there is a warning
        payment_line.amount_currency = 125
        onchange_res = payment_line._onchange_amount_with_discount()
        self.assertTrue("warning" in onchange_res)
        self.assertFalse(payment_line.pay_with_discount)

        # Change it back to use the discount
        payment_line.pay_with_discount = True
        payment_line._onchange_pay_with_discount()
        self.assertAlmostEqual(payment_line.amount_currency, 1500)
        payment_line.invalidate_cache()

        # Check pay_with_discount_constraint
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            payment_line.move_line_id = False

        # Change pay_with_discount and check if discount amount is coherent
        # with the invoice
        payment_line.pay_with_discount = False
        payment_line._onchange_pay_with_discount()
        self.assertEqual(payment_line.amount_currency, invoice.amount_total)

        payment_line.pay_with_discount = True
        payment_line._onchange_pay_with_discount()
        self.assertEqual(
            payment_line.amount_currency, invoice.amount_total - invoice.discount_amount
        )

        self.assertAlmostEqual(payment_line.discount_amount, 500, 2)
        self.assertAlmostEqual(payment_line.amount_currency, 1500, 2)
