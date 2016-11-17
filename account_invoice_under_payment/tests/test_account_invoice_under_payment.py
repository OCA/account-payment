# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
import datetime
from openerp import workflow


class TestAccountInvoiceUnderPayment(TransactionCase):

    def setUp(self):
        super(TestAccountInvoiceUnderPayment, self).setUp()
        self.account_invoice = self.env['account.invoice']
        self.payment_order = self.env['payment.order']
        self.account = self.env['account.account'].search(
            [('type', '=', 'payable'), ('currency_id', '=', False)],
            limit=1)[0]
        self.date_today = datetime.datetime.now()
        self.partner = self.env.ref('base.res_partner_1')
        self.uom_unit = self.env.ref('product.product_uom_unit')
        self.product_test = self.env['product.product'].create({
            'name': 'Test Product',
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'lst_price': 11.55})

        # Refs
        self.journal = self.env.ref('account.expenses_journal')
        self.user = self.env.ref('base.user_root')
        self.mode = self.env.ref('account_payment.payment_mode_1')

    def test_invoice_account(self):
        self.invoice = self.account_invoice.create({
            'partner_id': self.partner.id,
            'reference_type': 'none',
            'date_invoice': self.date_today,
            'date_due': self.date_today,
            'account_id': self.account.id,
            'journal_id': self.journal.id,
            'invoice_line': [(0, 0, {
                'product_id': self.product_test.id,
                'name': 'Test',
                'quantity': 10.0,
                'price_unit': 12.00
            })],
        })

        workflow.trg_validate(self.uid, 'account.invoice', self.invoice.id,
                              'invoice_open', self.cr)

        domain = [('invoice', '=', self.invoice.id),
                  ('reconcile_id', '=', False),
                  ('account_id.reconcile', '=', True)]
        self.move_line_id = self.env['account.move.line'].search(domain)

        self.payment = self.payment_order.create({
            'user_id': self.user.id,
            'date_prefered': 'due',
            'mode': self.mode.id,
            'date_scheduled': self.date_today
        })

        payment_line_record = self.env['payment.line'].new()
        payment_line_record.move_line_id = self.move_line_id.id
        res = payment_line_record.onchange_move_line(
            self.move_line_id.id,
            self.payment.mode.id,
            self.payment.date_prefered,
            self.payment.date_scheduled)
        if res.get('value') and res.get('value').get('communication'):
            bank_id = res.get('value').get('bank_id')
            currency = res.get('value').get('currency')
            amount = res.get('value').get('amount')
            date = res.get('value').get('date')
            amount_currency = res.get('value').get('amount_currency')
            communication = res.get('value').get('communication')
            partner_id = res.get('value').get('partner_id')
            self.env['payment.line'].create({
                'order_id': self.payment.id,
                'move_line_id': self.move_line_id.id,
                'bank_id': bank_id,
                'currency': currency,
                'amount': amount,
                'date': date,
                'amount_currency': amount_currency,
                'communication': communication,
                'partner_id': partner_id,
                'failed': False
            })
            # Check move line and invoice payment status
            self.assertEqual(True, self.move_line_id.under_payment)
            self.assertEqual(True, self.invoice.under_payment)

            self.payment.line_ids.set_failed()
            self.assertEqual(True, self.payment.line_ids.failed)
            self.assertEqual(False, self.move_line_id.under_payment)
            self.assertEqual(False, self.invoice.under_payment)
