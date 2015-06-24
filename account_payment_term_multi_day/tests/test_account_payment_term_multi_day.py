##############################################################################
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
import openerp.tests.common as common
from openerp import workflow


class TestAccountPaymentTermMultiDay(common.TransactionCase):

    def setUp(self):
        super(TestAccountPaymentTermMultiDay, self).setUp()
        self.payment_term_model = self.env['account.payment.term']
        self.invoice_model = self.env['account.invoice']
        self.journal = self.env.ref('account.sales_journal')
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref('product.product_product_5')
        self.account = self.env.ref('account.a_recv')
        self.payment_term_0_day_5 = self.payment_term_model.create(
            {"name": "Normal payment in day 5",
             "active": True,
             "line_ids": [(0, 0, {'value': 'balance',
                                  'days': 0,
                                  'days2': 5,
                                  })],
             })
        self.payment_term_0_days_5_10 = self.payment_term_model.create(
            {"name": "Payment for days 5 and 10",
             "active": True,
             "line_ids": [(0, 0, {'value': 'balance',
                                  'days': 0,
                                  'payment_days': '5,10',
                                  })],
             })

    def test_invoice_normal_payment_term(self):
        invoice = self.invoice_model.create(
            {'journal_id': self.journal.id,
             'partner_id': self.partner.id,
             'account_id': self.account.id,
             'payment_term': self.payment_term_0_day_5.id,
             'date_invoice': '%s-01-01' % datetime.now().year,
             'name': 'Invoice for normal payment on day 5',
             'invoice_line': [(0, 0, {'product_id': self.product.id,
                                      'name': 'Test',
                                      'quantity': 10.0,
                                      })],
             })
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        for line in invoice.move_id.line_id:
            if line.date_maturity:
                self.assertEqual(
                    line.date_maturity,
                    '%s-02-05' % datetime.now().year,
                    "Incorrect due date for invoice with normal payment day "
                    "on 5")

    def test_invoice_multi_payment_term_day_1(self):
        invoice = self.invoice_model.create(
            {'journal_id': self.journal.id,
             'partner_id': self.partner.id,
             'account_id': self.account.id,
             'payment_term': self.payment_term_0_days_5_10.id,
             'date_invoice': '%s-01-01' % datetime.now().year,
             'name': 'Invoice for payment on days 5 and 10 (1)',
             'invoice_line': [(0, 0, {'product_id': self.product.id,
                                      'name': 'Test',
                                      'quantity': 10.0,
                                      })],
             })
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        for line in invoice.move_id.line_id:
            if line.date_maturity:
                self.assertEqual(
                    line.date_maturity,
                    '%s-01-05' % datetime.now().year,
                    "Incorrect due date for invoice with payment days on 5 "
                    "and 10 (1)")

    def test_invoice_multi_payment_term_day_6(self):
        invoice = self.invoice_model.create(
            {'journal_id': self.journal.id,
             'partner_id': self.partner.id,
             'account_id': self.account.id,
             'payment_term': self.payment_term_0_days_5_10.id,
             'date_invoice': '%s-01-06' % datetime.now().year,
             'name': 'Invoice for payment on days 5 and 10 (2)',
             'invoice_line': [(0, 0, {'product_id': self.product.id,
                                      'name': 'Test',
                                      'quantity': 10.0,
                                      })],
             })
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        for line in invoice.move_id.line_id:
            if line.date_maturity:
                self.assertEqual(
                    line.date_maturity,
                    '%s-01-10' % datetime.now().year,
                    "Incorrect due date for invoice with payment days on 5 "
                    "and 10 (2)")

    def test_decode_payment_days(self):
        expected_days = [5, 10]
        model = self.env['account.payment.term.line']
        self.assertEqual(expected_days, model._decode_payment_days('5,10'))
        self.assertEqual(expected_days, model._decode_payment_days('5-10'))
        self.assertEqual(expected_days, model._decode_payment_days('5 10'))
        self.assertEqual(expected_days, model._decode_payment_days('10,5'))
        self.assertEqual(expected_days, model._decode_payment_days('10-5'))
        self.assertEqual(expected_days, model._decode_payment_days('10 5'))
        self.assertEqual(expected_days, model._decode_payment_days('5, 10'))
        self.assertEqual(expected_days, model._decode_payment_days('5 - 10'))
        self.assertEqual(expected_days, model._decode_payment_days('5    10'))
