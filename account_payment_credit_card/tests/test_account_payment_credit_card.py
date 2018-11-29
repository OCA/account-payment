# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo import fields


class TestAccountPaymentCreditCard(TransactionCase):

    def setUp(self):
        super(TestAccountPaymentCreditCard, self).setUp()

        self.journal_bank = self.env['account.journal'].create({
            'name': 'BANK Journal - Test',
            'code': 'AJ-BANK',
            'type': 'bank',
            'company_id': self.env.user.company_id.id,
            'credit_card': True,
        })

        self.move = self.env['account.move'].create({
            'name': fields.Date.today(),
            'journal_id': self.journal_bank.id,
            'ref': 'test',
        })

        self.move_line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'account_id': 1,
        })

    def test_post_check(self):
        self.move.post()
        self.assertTrue(self.move.journal_id.credit_card)
        self.assertEqual(len(self.move.line_ids), 2)
