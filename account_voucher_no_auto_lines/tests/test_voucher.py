# -*- coding: utf-8 -*-
# © 2016 Joao Alfredo Gama Batista, Kitti U.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from openerp.tests import common


class TestAccountVoucher(common.TransactionCase):

    def setUp(self):
        super(TestAccountVoucher, self).setUp()

        self.user_model = self.env['res.users']

        self.context = self.user_model.context_get()

        self.model = self.env['account.voucher']
        self.line = self.env['account.voucher.line']
        self.account_model = self.env['account.account']
        self.partner_model = self.env['res.partner']
        self.invoice_model = self.env['account.invoice']
        self.product_model = self.env['product.product']
        self.voucher_model = self.env['account.voucher']

        self.account = self.account_model.search(
            [('type', '=', 'payable'), ('currency_id', '=', False)],
            limit=1)[0]

        self.partner = self.partner_model.create(
            {
                'name': 'Test',
                'supplier': True,
            })

        self.invoice = self.invoice_model.create(
            {
                'partner_id': self.partner.id,
                'account_id': self.account.id,
                'date_invoice': str(date.today().year) + '-01-01',
                'invoice_line': [(0, 0, {
                    'name': 'Test',
                    'account_id': self.account.id,
                    'price_unit': 123.45,
                    'quantity': 1,
                })],
            })

        # Create accounting moves for the invoice
        self.invoice.signal_workflow('invoice_open')

        self.voucher = self.voucher_model.create(
            {
                'date': str(date.today().year) + '-01-02',
                'name': "test", 'amount': 200,
                'account_id': self.account.id,
                'partner_id': self.partner.id,
                'type': 'payment',
            })

    def createVoucher(self, **kwargs):
        """
        name required
        account_id required
        """
        return self.model.create(self.cr, self.uid, kwargs)

    def createLine(self, **kwargs):
        """
        voucher_id required
        account_id required
        """
        return self.line.create(self.cr, self.uid, kwargs)

    def test_onchange_amount(self):
        """
        Test if we can create an account
        and call the onchange_amount function and
        expect the returned value to have the same lines as
        before the call
        """

        voucher = self.voucher_model.browse(
            self.voucher.id)
        val = voucher.onchange_partner_id(
            self.partner.id,
            voucher.journal_id.id,
            voucher.amount,
            voucher.currency_id.id,
            voucher.type,
            voucher.date
        )

        debit = val['value']['line_dr_ids']
        credit = val['value']['line_cr_ids']

        self.assertEqual(debit[0]['amount'], 0)
        self.assertEqual(debit[0]['reconcile'], False)

        self.assertEqual(credit[0]['amount'], 0)
        self.assertEqual(credit[0]['reconcile'], False)
