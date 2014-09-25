# -*- coding: utf-8 -*-

from openerp.tests import common


class test_account_voucher(common.TransactionCase):

    def setUp(self):
        super(test_account_voucher, self).setUp()

        self.user_model = self.registry("res.users")

        self.context = self.user_model.context_get(self.cr, self.uid)

        self.model = self.registry('account.voucher')
        self.line = self.registry('account.voucher.line')

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
