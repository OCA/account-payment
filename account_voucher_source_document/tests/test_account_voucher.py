# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
