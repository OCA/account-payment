# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services S.L. (
# <http://www.eficent.com>).
# © 2016 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields
import openerp.tests.common as common
from datetime import date, timedelta
from openerp import workflow
from openerp import exceptions


class TestAccountDueListDaysOverdue(common.TransactionCase):

    def setUp(self):
        super(TestAccountDueListDaysOverdue, self).setUp()
        self.overdue_term_model = self.env['account.overdue.term']
        self.account_move_line_model = self.env['account.move.line']
        self.account_invoice_model = self.env['account.invoice']
        self.account_invoice_line_model = self.env['account.invoice.line']
        self.overdue_term_1 = self.env.ref(
            'account_due_list_days_overdue.overdue_term_1')
        self.partner_agrolait = self.env.ref('base.res_partner_1')
        self.currency_usd = self.env.ref('base.USD')
        self.account_rcv = self.env.ref('account.a_recv')
        self.payment_term = self.env.ref('account.account_payment_term_15days')
        self.product = self.env.ref('product.product_product_4')

        # we create an invoice
        inv_date = date.today() - timedelta(days=16)
        self.invoice = self.account_invoice_model.create({
            'partner_id': self.partner_agrolait.id,
            'reference_type': 'none',
            'currency_id': self.currency_usd.id,
            'name': 'invoice to customer',
            'payment_term': self.payment_term.id,
            'account_id': self.account_rcv.id,
            'type': 'out_invoice',
            'date_invoice': fields.Date.to_string(inv_date),
            })

        self.account_invoice_line_model.create({'product_id': self.product.id,
                                                'quantity': 1,
                                                'price_unit': 100,
                                                'invoice_id': self.invoice.id,
                                                'name': 'product that cost 100'
                                                })
        workflow.trg_validate(self.uid, 'account.invoice', self.invoice.id,
                              'invoice_open', self.cr)

    def test_due_days(self):
        move = self.invoice.move_id
        for line in move.line_id:
            if line.account_id == self.account_rcv:
                self.assertEqual(line.days_overdue, 1,
                                 'Incorrect calculation of number of days '
                                 'overdue')

    def test_overdue_term(self):
        move = self.invoice.move_id
        self.account_move_line_model._register_hook()
        for line in move.line_id:
            if line.account_id == self.account_rcv:
                self.assertEqual(
                    line[self.overdue_term_1.tech_name], line.amount_residual,
                    'Overdue term 1-30 should contain a due amount')

    def test_ovelapping_overdue_term(self):
        with self.assertRaises(exceptions.ValidationError):
            self.overdue_term_test = self.overdue_term_model.create({
                "name": "25-30",
                "from_day": 25,
                "to_day": 30
            })
