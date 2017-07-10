# -*- coding: utf-8 -*-
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .test_import_file import TestPaymentReturnFile
from odoo.exceptions import UserError


class TestImport(TestPaymentReturnFile):
    """Run test to import payment return import."""

    def setUp(self):
        super(TestImport, self).setUp()
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

    def test_payment_return_import(self):
        with self.assertRaises(UserError):
            self._test_return_import(
                'account_payment_return_import', 'test_empty.csv',
                'TEST123456',
                local_account='NL77ABNA0574908765',
            )

    def test_zip_import(self):
        with self.assertRaises(UserError):
            self._test_return_import(
                'account_payment_return_import',
                'test_01.zip',
                'TEST123456',
                local_account='NL77ABNA0574908765',
            )
