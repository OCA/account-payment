# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import workflow
from openerp.tests import common


class TestAccountVoucher(common.TransactionCase):

    def setUp(self):
        super(TestAccountVoucher, self).setUp()

        self.user_model = self.env["res.users"]

        self.env.user.company_id.disable_voucher_auto_lines = True

        self.account = self.env['account.account'].search(
            [('type', '=', 'payable'), ('currency_id', '=', False)],
            limit=1)[0]

        self.account_expense = self.env['account.account'].search(
            [('type', '=', 'other'), ('currency_id', '=', False)],
            limit=1)[0]

        self.partner = self.env['res.partner'].create({
            'name': 'Test',
            'supplier': True,
        })

    def create_invoice(self, invoice_type, amount):
        year = datetime.now().year

        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account.id,
            'date_invoice': '%s-01-01' % year,
            'type': invoice_type,
            'supplier_invoice_number': 'TEST1234',
            'invoice_line': [(0, 0, {
                'name': 'Test',
                'account_id': self.account_expense.id,
                'price_unit': amount,
                'quantity': 1,
            })],
        })

        workflow.trg_validate(
            self.uid, 'account.invoice', self.invoice.id,
            'invoice_open', self.cr)

        self.voucher = self.env['account.voucher'].create({
            'date': '%s-01-02' % year,
            'name': "test",
            'account_id': self.account.id,
            'partner_id': self.partner.id,
            'type': 'payment',
        })

    def test_01_voucher_line_supplier_invoice_number(self):
        self.create_invoice('in_invoice', 100)
        v = self.voucher
        onchange_res = v.onchange_partner_id(
            v.partner_id.id, v.journal_id.id, v.amount, v.currency_id.id,
            v.type, v.date)

        lines = [(0, 0, l) for l in onchange_res['value']['line_dr_ids']]
        self.assertEqual(lines[0][2]['supplier_invoice_number'], 'TEST1234')
        self.voucher.write({'line_cr_ids': lines})

        voucher_line = self.voucher.line_ids[0]
        self.assertEqual(voucher_line.supplier_invoice_number, 'TEST1234')

        self.invoice.write({'supplier_invoice_number': 'TEST5678'})
        self.assertEqual(voucher_line.supplier_invoice_number, 'TEST5678')

    def test_02_voucher_line_supplier_invoice_number_refund(self):
        self.create_invoice('in_refund', 100)
        v = self.voucher
        onchange_res = v.onchange_partner_id(
            v.partner_id.id, v.journal_id.id, v.amount, v.currency_id.id,
            v.type, v.date)

        lines = [(0, 0, l) for l in onchange_res['value']['line_cr_ids']]
        self.assertEqual(lines[0][2]['supplier_invoice_number'], 'TEST1234')
        self.voucher.write({'line_cr_ids': lines})

        voucher_line = self.voucher.line_ids[0]
        self.assertEqual(voucher_line.supplier_invoice_number, 'TEST1234')

        self.invoice.write({'supplier_invoice_number': 'TEST5678'})
        self.assertEqual(voucher_line.supplier_invoice_number, 'TEST5678')
