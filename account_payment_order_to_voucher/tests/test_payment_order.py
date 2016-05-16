# -*- coding: utf-8 -*-
#
#   See __openerp__.py about license
#

from openerp.tests.common import TransactionCase
from openerp import fields


class TestOrder(TransactionCase):

    def test_payment_order(self):
        demo_invoice_0 = self.env.ref('account.demo_invoice_0')
        payment_order_1 = self.env.ref('account_payment.payment_order_1')
        payment_wizard = self.env['payment.order.create'].with_context({
            'active_model': 'payment.order',
            'active_ids': [payment_order_1.id],
            'active_id': payment_order_1.id,
        })
        cr, uid = self.cr, self.uid
        demo_invoice_0.check_total = 14
        self.registry('account.invoice').signal_workflow(
            cr, uid, [demo_invoice_0.id], 'invoice_open')
        self.registry('payment.order').signal_workflow(
            cr, uid, [payment_order_1.id], 'open')
        wizard = payment_wizard.create({
            'duedate': fields.Date.today(),
            'entries': [(6, 0, [demo_invoice_0.move_id.line_id[0].id])]
            })
        wizard.create_payment()
        payment_order_1.set_done()
        payment_order_1.generate_vouchers()
        self.assertEqual(len(payment_order_1.voucher_ids), 1)
        payment_order_1.voucher_ids[0].proforma_voucher()
        self.assertEqual(demo_invoice_0.state, 'paid')
