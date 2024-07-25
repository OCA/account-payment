# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestAccountPaymentReturnImport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.return_import_model = cls.env["payment.return.import"]
        cls.company = cls.env.ref("base.main_company")
        cls.acc_number = "NL77ABNA0574908765"
        cls.acc_bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "acc_number": cls.acc_number,
                "bank_name": "TEST BANK",
                "company_id": cls.company.id,
            }
        )
        cls.journal = cls.acc_bank.journal_id

    def test_get_journal(self):
        bank_account_id = self.return_import_model._find_bank_account_id(
            self.acc_number
        )
        journal_id = self.return_import_model._get_journal(bank_account_id)
        self.assertEqual(journal_id, self.journal.id)
