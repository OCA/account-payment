# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Date
from .common import TestAccountCashDiscountPaymentCommon


class TestAccountCashDiscountPayment(TestAccountCashDiscountPaymentCommon):

    def test_invoice_payment_discount(self):
        invoice_date = Date.today()
        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 2000, 25, [])
        invoice.action_invoice_open()

        move = invoice.move_id
        move.post()

        payment_order = self.PaymentOrder.create({
            'payment_mode_id': self.payment_mode_out.id,
            'payment_type': 'outbound',
        })

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create({
            'cash_discount_date_start': invoice_date,
            'cash_discount_date_end': invoice_date,
            'date_type': 'discount_due_date',
            'journal_ids': [(6, 0, [self.purchase_journal.id])],
        })
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        move_lines = payment_line_wizard.move_line_ids
        self.assertEqual(len(move_lines), 1)

        move_line = move_lines[0]
        self.assertAlmostEqual(move_line.discount_amount, 500, 2)

        payment_line_wizard.create_payment_lines()

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        move_line = payment_order.payment_line_ids[0]
        self.assertTrue(move_line.pay_with_discount)
        self.assertAlmostEqual(move_line.discount_amount, 500, 2)
        self.assertAlmostEqual(move_line.amount_currency, 1500, 2)
