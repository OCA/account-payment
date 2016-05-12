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

        year = datetime.now().year

        self.account = self.env['account.account'].search(
            [('type', '=', 'receivable'), ('currency_id', '=', False)],
            limit=1)[0]

        self.partner = self.env['res.partner'].create({
            'name': 'Test',
            'customer': True,
        })

        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account.id,
            'date_invoice': '%s-01-01' % year,
            'type': 'out_invoice',
            'origin': 'TEST1234',
            'invoice_line': [(0, 0, {
                'name': 'Test',
                'account_id': self.account.id,
                'price_unit': 123.45,
                'quantity': 1,
            })],
        })

        workflow.trg_validate(
            self.uid, 'account.invoice', self.invoice.id,
            'invoice_open', self.cr)

        self.voucher = self.env['account.voucher'].create({
            'date': '%s-01-02' % year,
            'name': "test", 'amount': 200,
            'account_id': self.account.id,
            'partner_id': self.partner.id,
            'type': 'receipt',
        })

        v = self.voucher
        onchange_res = v.onchange_partner_id(
            v.partner_id.id, v.journal_id.id, v.amount, v.currency_id.id,
            v.type, v.date)

        lines = [(0, 0, l) for l in onchange_res['value']['line_cr_ids']]
        self.voucher.write({'line_cr_ids': lines})

    def test_01_voucher_line_source_document(self):
        voucher_line = self.voucher.line_ids[0]
        self.assertEqual(voucher_line.document_source, 'TEST1234')

        self.invoice.write({'origin': 'TEST5678'})
        self.assertEqual(voucher_line.document_source, 'TEST5678')
