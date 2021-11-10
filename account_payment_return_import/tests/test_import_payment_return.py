# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountPaymentReturnImport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.return_import_model = self.env["payment.return.import"]
        self.company = self.env.ref("base.main_company")
        self.acc_number = "NL77ABNA0574908765"
        self.acc_bank = self.env["res.partner.bank"].create(
            {
                "partner_id": self.company.partner_id.id,
                "acc_number": self.acc_number,
                "bank_name": "TEST BANK",
                "company_id": self.company.id,
            }
        )
        self.journal = self.acc_bank.journal_id

    def test_get_journal(self):
        bank_account_id = self.return_import_model._find_bank_account_id(
            self.acc_number
        )
        journal_id = self.return_import_model._get_journal(bank_account_id)
        self.assertEqual(journal_id, self.journal.id)
