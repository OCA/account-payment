# -*- coding: utf-8 -*-
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .test_import_file import TestPaymentReturnFile
from odoo.exceptions import UserError


class TestImportBase(TestPaymentReturnFile):
    """Run test to import payment return import."""

    def setUp(self):
        super(TestImportBase, self).setUp()
        self.company = self.env.ref('base.main_company')
        self.acc_number = 'NL77ABNA0574908765'
        self.acc_bank = self.env['res.partner.bank'].create({
            'acc_number': self.acc_number,
            'bank_name': 'TEST BANK',
            'company_id': self.company.partner_id.id,
            'partner_id': self.company.partner_id.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test Bank Journal',
            'code': 'BANK',
            'type': 'bank',
            'update_posted': True,
            'bank_account_id': self.acc_bank.id,
        })
        self.journal.bank_account_id = self.acc_bank
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.reason = self.env['payment.return.reason'].create({
            'code': 'RTEST',
            'name': 'Reason Test'
        })
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test',
            'type': 'receivable',
        })
        self.account = self.env['account.account'].create({
            'name': 'Test account',
            'code': 'TEST',
            'user_type_id': self.account_type.id,
            'reconcile': True,
        })
        self.account_income = self.env['account.account'].create({
            'name': 'Test income account',
            'code': 'INCOME',
            'user_type_id': self.env['account.account.type'].create(
                {'name': 'Test income'}).id,
        })
        self.invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'account_id': self.account.id,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'account_id': self.account_income.id,
                'name': 'Test line',
                'price_unit': 250.9,
                'quantity': 1,
            })]
        })
        self.invoice.action_invoice_open()
        self.receivable_line = self.invoice.move_id.line_ids.filtered(
            lambda x: x.account_id.internal_type == 'receivable')
        # Invert the move to simulate the payment
        self.payment_move = self.invoice.move_id.copy({
            'journal_id': self.journal.id
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
