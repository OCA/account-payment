# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp import workflow


class test_account_voucher(common.TransactionCase):

    def setUp(self):
        super(test_account_voucher, self).setUp()

        self.user_model = self.env["res.users"]
        self.line = self.env['account.voucher.line']
        self.account_model = self.env['account.account']
        self.partner_model = self.env['res.partner']
        self.invoice_model = self.env['account.invoice']
        self.product_model = self.env['product.product']
        self.voucher_model = self.env['account.voucher']

        self.account = self.account_model.search(
            [('type', '=', 'payable'), ('currency_id', '=', False)],
            limit=1)[0]

        self.partner = self.partner_model.create({
            'name': 'Test',
            'supplier': True,
        })

        self.invoice = self.invoice_model.create({
            'partner_id': self.partner.id,
            'account_id': self.account.id,
            'date_invoice': '2015-01-01',
            'type': 'in_invoice',
            'invoice_line': [(0, 0, {
                'name': 'Test',
                'account_id': self.account.id,
                'price_unit': 123.45,
                'quantity': 1,
            })],
        })

        # Create accounting moves for the invoice
        workflow.trg_validate(
            self.uid, 'account.invoice', self.invoice.id,
            'invoice_open', self.cr)

        self.voucher = self.voucher_model.create({
            'date': '2015-01-02',
            'name': "test", 'amount': 200,
            'account_id': self.account.id,
            'partner_id': self.partner.id,
            'type': 'payment',
        })

    def test_01_onchange_partner_id(self):
        v = self.voucher
        res = v.onchange_partner_id(
            v.partner_id.id, v.journal_id.id, v.amount, v.currency_id.id,
            v.type, v.date)

        voucher_line = res['value']['line_dr_ids'][0]

        self.assertEqual(voucher_line['amount'], 0)
        self.assertEqual(voucher_line['reconcile'], False)

    def test_02_onchange_partner_id_allow_auto_lines(self):
        v = self.voucher
        res = v.with_context({'allow_auto_lines': True}).onchange_partner_id(
            v.partner_id.id, v.journal_id.id, v.amount, v.currency_id.id,
            v.type, v.date)

        voucher_line = res['value']['line_dr_ids'][0]

        self.assertEqual(voucher_line['amount'], 123.45)
        self.assertEqual(voucher_line['reconcile'], True)

    def test_03_onchange_amount(self):
        v = self.voucher
        res = v.onchange_amount(
            v.amount, 1, v.partner_id.id, v.journal_id.id,
            v.currency_id.id, v.type, v.date,
            v.payment_rate_currency_id.id, v.company_id.id
        )

        self.assertNotIn('line_dr_ids', res['value'])
        self.assertNotIn('line_cr_ids', res['value'])

    def test_04_onchange_amount_allow_auto_lines(self):
        v = self.voucher
        res = v.with_context({'allow_auto_lines': True}).onchange_amount(
            v.amount, 1, v.partner_id.id, v.journal_id.id,
            v.currency_id.id, v.type, v.date,
            v.payment_rate_currency_id.id, v.company_id.id
        )

        voucher_line = res['value']['line_dr_ids'][0]

        self.assertEqual(voucher_line['amount'], 123.45)
        self.assertEqual(voucher_line['reconcile'], True)

    def test_05_onchange_journal(self):
        v = self.voucher

        vals = v.onchange_amount(
            v.amount, 1, v.partner_id.id, v.journal_id.id,
            v.currency_id.id, v.type, v.date,
            v.payment_rate_currency_id.id, v.company_id.id
        )['value']

        v.write(vals)
        v.refresh()

        res = v.onchange_journal(
            v.journal_id.id, v.line_ids, v.tax_id.id, v.partner_id.id,
            v.date, v.amount, v.type, v.company_id.id
        )

        voucher_line = res['value']['line_dr_ids'][0]

        self.assertEqual(voucher_line['amount'], 0)
        self.assertEqual(voucher_line['reconcile'], False)

        context = {'line_dr_ids': [(0, 0, voucher_line)]}
        voucher_line['amount'] = 90

        res = v.with_context(context).onchange_journal(
            v.journal_id.id, v.line_ids, v.tax_id.id, v.partner_id.id,
            v.date, v.amount, v.type, v.company_id.id
        )

        voucher_line = next(
            l for l in res['value']['line_dr_ids'] if isinstance(l, dict))

        self.assertEqual(voucher_line['amount'], 90)
        self.assertEqual(voucher_line['reconcile'], False)

    def test_06_onchange_journal_allow_auto_lines(self):
        v = self.voucher.with_context({'allow_auto_lines': True})

        vals = v.onchange_amount(
            v.amount, 1, v.partner_id.id, v.journal_id.id,
            v.currency_id.id, v.type, v.date,
            v.payment_rate_currency_id.id, v.company_id.id
        )['value']

        vals['line_dr_ids'] = [(0, 0, line) for line in vals['line_dr_ids']]
        vals['line_cr_ids'] = [(0, 0, line) for line in vals['line_cr_ids']]

        v.write(vals)
        v.refresh()

        res = v.onchange_journal(
            v.journal_id.id, v.line_ids, v.tax_id.id, v.partner_id.id,
            v.date, v.amount, v.type, v.company_id.id
        )

        voucher_line = next(
            l for l in res['value']['line_dr_ids'] if isinstance(l, dict))

        self.assertEqual(voucher_line['amount'], 123.45)
        self.assertEqual(voucher_line['reconcile'], True)
