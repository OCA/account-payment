# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .test_import_file import TestPaymentReturnFile
from odoo.exceptions import UserError


class TestImportBase(TestPaymentReturnFile):
    """Run test to import payment return import."""

    @classmethod
    def setUpClass(cls):
        super(TestImportBase, cls).setUpClass()
        cls.company = cls.env.ref('base.main_company')
        cls.acc_number = 'NL77ABNA0574908765'
        cls.acc_bank = cls.env['res.partner.bank'].create({
            'acc_number': cls.acc_number,
            'bank_name': 'TEST BANK',
            'company_id': cls.company.id,
            'partner_id': cls.company.partner_id.id,
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test Bank Journal',
            'code': 'BANK',
            'type': 'bank',
            'update_posted': True,
            'bank_account_id': cls.acc_bank.id,
        })
        cls.journal.bank_account_id = cls.acc_bank
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test partner',
        })
        cls.reason = cls.env['payment.return.reason'].create({
            'code': 'RTEST',
            'name': 'Reason Test'
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test',
            'type': 'receivable',
        })
        cls.account = cls.env['account.account'].create({
            'name': 'Test account',
            'code': 'TEST',
            'user_type_id': cls.account_type.id,
            'reconcile': True,
        })
        cls.account_income = cls.env['account.account'].create({
            'name': 'Test income account',
            'code': 'INCOME',
            'user_type_id': cls.env['account.account.type'].create(
                {'name': 'Test income'}).id,
        })
        cls.invoice = cls.env['account.invoice'].create({
            'journal_id': cls.journal.id,
            'account_id': cls.account.id,
            'company_id': cls.env.user.company_id.id,
            'currency_id': cls.env.user.company_id.currency_id.id,
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'account_id': cls.account_income.id,
                'name': 'Test line',
                'price_unit': 250.9,
                'quantity': 1,
            })]
        })
        cls.invoice.action_invoice_open()
        cls.receivable_line = cls.invoice.move_id.line_ids.filtered(
            lambda x: x.account_id.internal_type == 'receivable')
        # Invert the move to simulate the payment
        cls.payment_move = cls.invoice.move_id.copy({
            'journal_id': cls.journal.id
        })

    def test_payment_return_import(self):
        self._test_return_import(
            'account_payment_return_import', 'test_payment_import.csv',
            'M00000123',
            local_account='NL77ABNA0574908765',
        )

    def test_zipped_payment_return_import(self):
        self._test_return_import(
            'account_payment_return_import', 'test_payment_import.zip',
            'M00000123',
            local_account='NL77ABNA0574908765',
        )

    def test_payment_return_import_empty(self):
        with self.assertRaises(UserError):
            self._test_return_import(
                'account_payment_return_import', 'test_empty.csv',
                'TEST123456',
                local_account='NL77ABNA0574908765',
            )

    def test_zip_import_empty(self):
        with self.assertRaises(UserError):
            self._test_return_import(
                'account_payment_return_import',
                'test_zipped_payment_import_empty.zip',
                'TEST123456',
                local_account='NL77ABNA0574908765',
            )
