# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp import netsvc


class test_account_voucher(common.TransactionCase):

    def setUp(self):
        super(test_account_voucher, self).setUp()

        self.user_model = self.registry("res.users")

        self.context = self.user_model.context_get(self.cr, self.uid)

        self.model = self.registry('account.voucher')
        self.line = self.registry('account.voucher.line')
        self.account_model = self.registry('account.account')
        self.partner_model = self.registry('res.partner')
        self.invoice_model = self.registry('account.invoice')
        self.product_model = self.registry('product.product')
        self.voucher_model = self.registry('account.voucher')

        cr, uid, context = self.cr, self.uid, self.context

        self.account_id = self.account_model.search(
            cr, uid, [('type', '=', 'payable'), ('currency_id', '=', False)],
            limit=1, context=context)[0]

        self.partner_id = self.partner_model.create(
            cr, uid, {
                'name': 'Test',
                'supplier': True,
            }, context=context)

        self.invoice_id = self.invoice_model.create(
            cr, uid, {
                'partner_id': self.partner_id,
                'account_id': self.account_id,
                'date_invoice': '2015-01-01',
                'invoice_line': [(0, 0, {
                    'name': 'Test',
                    'account_id': self.account_id,
                    'price_unit': 123.45,
                    'quantity': 1,
                })],
            }, context=context)

        # Create accounting moves for the invoice
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(
            uid, 'account.invoice', self.invoice_id, 'invoice_open', cr)

        self.voucher_id = self.voucher_model.create(
            cr, uid, {
                'date': '2015-01-02',
                'name': "test", 'amount': 200,
                'account_id': self.account_id,
                'partner_id': self.partner_id,
                'type': 'payment',
            }, context=context)

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

        voucher_id = self.createVoucher(name="test",
                                        amount=0,
                                        account_id=self.uid)

        voucher = self.model.read(self.cr, self.uid, voucher_id)

        self.assertEqual(voucher['line_cr_ids'], [])
        self.assertEqual(voucher['line_dr_ids'], [])

        self.model.write(self.cr, self.uid, voucher_id, {
            "amount": 100,
        })

        voucher = self.model.read(self.cr, self.uid, voucher_id)

        self.assertEqual(voucher['amount'], 100)
        self.assertEqual(voucher['line_cr_ids'], [])
        self.assertEqual(voucher['line_dr_ids'], [])

        line1 = self.createLine(voucher_id=voucher_id,
                                type="cr",
                                amount=123.45,
                                account_id=self.uid)

        line_record = self.line.read(self.cr, self.uid, line1)
        voucher = self.model.read(self.cr, self.uid, voucher_id)

        self.assertNotEqual(line1, 0)
        self.assertEqual(line_record['type'], 'cr')

        self.assertEqual(len(voucher['line_cr_ids']), 1)
        self.assertEqual(voucher['line_cr_ids'][0], line1)
        self.assertEqual(voucher['line_dr_ids'], [])

        self.model.write(self.cr, self.uid, voucher_id, {
            "amount": 123.46
        })

        voucher = self.model.browse(self.cr, self.uid, voucher_id)

        val = voucher.onchange_amount(
            voucher.amount,
            voucher.payment_rate,
            voucher.partner_id.id,
            voucher.journal_id.id,
            voucher.currency_id.id,
            'payment',
            voucher.date,
            voucher.payment_rate_currency_id.id,
            voucher.company_id.id,
            context=self.context
        )

        voucher = self.model.read(self.cr, self.uid, voucher_id)

        self.assertEqual(voucher['line_cr_ids'], [])
        self.assertEqual(voucher['line_dr_ids'], [])

        credit = val['value']['line_cr_ids']
        debit = val['value']['line_dr_ids']

        self.assertEqual(len(credit), 1)
        self.assertEqual(len(debit), 0)

        self.assertEqual(voucher['amount'], 123.46)
        self.assertEqual(credit[0]['amount'], 123.45)
