# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

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
        cr, uid, context = self.cr, self.uid, self.context

        voucher = self.voucher_model.browse(
            cr, uid, self.voucher_id, context=context)

        val = voucher.onchange_partner_id(
            self.partner_id,
            voucher.journal_id.id,
            voucher.amount,
            voucher.currency_id.id,
            voucher.type,
            voucher.date,
            context=context
        )

        debit = val['value']['line_dr_ids']
        credit = val['value']['line_cr_ids']

        self.assertEqual(debit[0]['amount'], 0)
        self.assertEqual(debit[0]['reconcile'], False)

        self.assertEqual(credit[0]['amount'], 0)
        self.assertEqual(credit[0]['reconcile'], False)
