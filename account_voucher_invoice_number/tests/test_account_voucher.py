# -*- coding: utf-8 -*-
# © 2015 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common
from openerp import workflow


class TestAccountVoucher(common.TransactionCase):

    def setUp(self):
        super(TestAccountVoucher, self).setUp()
        self.invoice_model = self.env['account.invoice']
        self.voucher_model = self.env['account.voucher']
        self.journal = self.env.ref('account.sales_journal')
        self.bank_journal = self.env.ref('account.bank_journal')
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref('product.product_product_5')
        self.account = self.env.ref('account.a_recv')
        self.eur = self.env.ref('base.EUR')

    def test_voucher(self):
        invoice = self.invoice_model.create(
            {'journal_id': self.journal.id,
             'partner_id': self.partner.id,
             'account_id': self.account.id,
             'invoice_line': [(0, 0, {'product_id': self.product.id,
                                      'name': 'Test',
                                      'quantity': 10.0,
                                      'price_unit': 100.0,
                                      })],
             })
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        res = invoice.invoice_pay_customer()
        vals = {
            'partner_id': res['context']['default_partner_id'],
            'amount': res['context']['default_amount'],
            'reference': res['context']['default_reference'],
            'type': res['context']['default_type'],
            'journal_id': self.bank_journal.id,
            'account_id': self.bank_journal.default_debit_account_id.id,
            }
        vals.update(self.voucher_model.with_context(
            res['context']
        ).recompute_voucher_lines(
            self.partner.id, self.bank_journal.id,
            res['context']['default_amount'], self.eur.id, 'receipt',
            False)['value'])
        vals['line_cr_ids'] = [(0, 0, vals['line_cr_ids'][0])]
        voucher = self.voucher_model.with_context(res['context']).create(vals)
        workflow.trg_validate(self.uid, 'account.voucher', voucher.id,
                              'proforma_voucher', self.cr)
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(voucher.invoices, invoice.number)
