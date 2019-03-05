# Copyright 2019 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.tests.common as common
from odoo import fields


class TestAccountReceiptPrint(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountReceiptPrint, cls).setUpClass()

        journal = cls.env['account.journal'].create({
            'name': 'Journal Test',
            'code': 'TEST',
            'type': 'cash',
        })
        partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        product = cls.env['product.product'].create({
            'name': 'Product Test',
        })
        account = cls.env['account.account'].create({
            'name': 'Account Test',
            'code': 'Test',
            'user_type_id': cls.env.ref(
                'account.data_account_type_receivable').id,
            'reconcile': True,
        })
        cls.invoice = cls.env['account.invoice'].create({
            'partner_id': partner.id,
            'account_id': account.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'account_id': account.id,
                'price_unit': 100.0,
                'quantity': 1.0,
            })]
        })
        cls.statement = cls.env['account.bank.statement'].create({
            'name': 'Statement Test',
            'journal_id': journal.id,
            'line_ids': [(0, 0, {
                'date': fields.Date.today(),
                'name': 'Line Test',
                'amount': -100.0,
                'partner_id': partner.id,
            })]
        })
        cls.payment = cls.env['account.payment'].create({
            'name': 'Payment Test',
            'payment_method_id': cls.env.ref(
                'account.account_payment_method_manual_in').id,
            'amount': 100.0,
            'payment_type': 'inbound',
            'journal_id': journal.id,
            'partner_type': 'customer',
        })

    def test_account_payment_print(self):
        result = self.payment.action_print_invoice_payment()
        self.assertEqual(result['name'], 'Account Payment Receipt')

    def test_account_payment_invoice_print(self):
        self.invoice.action_invoice_open()
        self.payment.invoice_ids = [(6, 0, self.invoice.ids)]
        self.invoice.state = 'open'
        line = self.statement.mapped('line_ids')
        line.auto_reconcile()
        result = line.action_print_invoice_payment()
        self.assertEqual(result['name'], 'Account Payment Receipt')
        result = self.payment.action_validate_print_invoice_payment()
        self.assertEqual(result['name'], 'Account Payment Receipt')
        self.assertEqual(self.invoice.state, 'paid')
