# -*- coding: utf-8 -*-
# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.account_payment_return_import.tests import (
    TestPaymentReturnFile)


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
        """Test correct creation of single payment return."""
        transactions = [
            {
                'returned_amount': 100.00,
                'reference': 'E2EID1',
            },
        ]
        self._test_return_import(
            'account_payment_return_import_sepa_pain', 'test-sepa-unpaid.xml',
            'MSGID99345678912',
            local_account='NL77ABNA0574908765',
            date='2016-10-08', transactions=transactions
        )

    def test_zip_import(self):
        """Test import of multiple statements from zip file."""
        self._test_return_import(
            'account_payment_return_import_sepa_pain', 'test-sepa-unpaid.zip',
            'MSGID99345678912',
            local_account='NL77ABNA0574908765',
            date='2016-10-08'
        )
