# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.exceptions import Warning as UserError
from openerp.tests.common import SavepointCase


class TestPaymentReturn(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPaymentReturn, cls).setUpClass()
        cls.account_invoice_model = cls.env['account.invoice']
        cls.payment_return_model = cls.env['payment.return']
        cls.partner = cls.env.ref('base.res_partner_1')
        # Prepare invoice and pay it for making the return
        cls.invoice = cls.env.ref('account.invoice_2')
        cls.invoice.journal_id.update_posted = True
        cls.invoice.signal_workflow('invoice_open')
        cls.receivable_line = cls.invoice.move_id.line_id.filtered(
            lambda x: x.account_id.type == 'receivable')
        # Invert the move to simulate the payment
        cls.payment_move = cls.invoice.move_id.copy()
        for move_line in cls.payment_move.line_id:
            debit = move_line.debit
            move_line.write({'debit': move_line.credit,
                             'credit': debit})
        cls.payment_line = cls.payment_move.line_id.filtered(
            lambda x: x.account_id.type == 'receivable')
        # Reconcile both
        cls.reconcile = cls.env['account.move.reconcile'].create(
            {'type': 'manual',
             'line_id': [(4, cls.payment_line.id),
                         (4, cls.receivable_line.id)]})
        # Create payment return
        cls.payment_return = cls.payment_return_model.create(
            {'journal_id': cls.env.ref('account.bank_journal').id,
             'line_ids': [
                 (0, 0, {'partner_id': cls.partner.id,
                         'move_line_ids': [(6, 0, cls.payment_line.ids)],
                         'amount': cls.payment_line.credit})]})
        cls.payment_return.journal_id.update_posted = True

    def test_confirm_error(self):
        self.payment_return.line_ids[0].move_line_ids = False
        with self.assertRaises(UserError):
            self.payment_return.action_confirm()

    def test_onchange_move_line(self):
        with self.env.do_in_onchange():
            record = self.env['payment.return.line'].new()
            record.move_line_ids = self.payment_line.ids
            record._onchange_move_line()
            self.assertEqual(record.amount, self.payment_line.credit)

    def test_payment_return(self):
        self.payment_return.action_cancel()  # No effect
        self.assertEqual(self.invoice.state, 'paid')
        self.assertEqual(self.payment_return.state, 'draft')
        self.payment_return.action_confirm()
        self.assertEqual(self.payment_return.state, 'done')
        self.assertEqual(self.invoice.state, 'open')
        self.assertEqual(self.invoice.residual, self.receivable_line.debit)
        self.assertEqual(
            len(self.receivable_line.reconcile_partial_id.line_partial_ids), 3)
        with self.assertRaises(UserError):
            self.payment_return.unlink()
        self.payment_return.action_cancel()
        self.assertEqual(self.payment_return.state, 'cancelled')
        self.assertEqual(self.invoice.state, 'paid')
        self.payment_return.action_draft()
        self.assertEqual(self.payment_return.state, 'draft')
        self.payment_return.unlink()

    def test_payment_partial_return(self):
        self.payment_return.line_ids[0].amount = 5.0
        self.assertEqual(self.invoice.state, 'paid')
        self.payment_return.action_confirm()
        self.assertEqual(self.invoice.state, 'open')
        self.assertEqual(self.invoice.residual, 5.0)
        self.assertEqual(
            len(self.receivable_line.reconcile_partial_id.line_partial_ids), 3)
        self.payment_return.action_cancel()
        self.assertEqual(self.invoice.state, 'paid')

    def test_find_match_invoice(self):
        self.payment_return.line_ids.write({
            'partner_id': False,
            'move_line_ids': [(6, 0, [])],
            'amount': 0.0,
            'reference': self.invoice.number,
        })
        self.payment_return.button_match()
        self.assertAlmostEqual(
            self.payment_return.line_ids[0].amount, self.payment_line.credit)

    def test_find_match_move_line(self):
        self.payment_line.name = 'test match move line 001'
        self.payment_return.line_ids.write({
            'partner_id': False,
            'move_line_ids': [(6, 0, [])],
            'amount': 0.0,
            'reference': self.payment_line.name,
        })
        self.payment_return.button_match()
        self.assertEqual(self.payment_return.line_ids[0].partner_id.id,
                         self.payment_line.partner_id.id)

    def test_find_match_move(self):
        self.payment_move.name = 'TESTMOVEXX01'
        self.payment_return.write({
            'line_ids': [
                (0, 0, {
                    'partner_id': False,
                    'move_line_ids': [(6, 0, [])],
                    'amount': 0.0,
                    'reference': self.payment_move.name,
                })]
        })
        with self.assertRaises(UserError):
            self.payment_return.button_match()
