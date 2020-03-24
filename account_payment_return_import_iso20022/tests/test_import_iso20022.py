# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError

from odoo.addons.account_payment_return_import.tests import TestPaymentReturnFile


class TestImport(TestPaymentReturnFile):
    """Run test to import payment return import."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.acc_number = "NL77ABNA0574908765"
        cls.acc_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": cls.acc_number,
                "bank_name": "TEST BANK",
                "company_id": cls.company.partner_id.id,
                "partner_id": cls.company.partner_id.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test Bank Journal",
                "code": "BANK",
                "type": "bank",
                "bank_account_id": cls.acc_bank.id,
            }
        )
        cls.journal.bank_account_id = cls.acc_bank

    def test_payment_return_import_pain(self):
        """Test correct creation of single payment return."""
        transactions = [
            {
                "returned_amount": 100.00,
                "reference": "E2EID1",
                "reason_add_info": "ACC NUMBER INVALID",
            },
        ]
        self._test_return_import(
            "account_payment_return_import_iso20022",
            "test-sepa-pain-unpaid.xml",
            "MSGID99345678912",
            local_account="NL77ABNA0574908765",
            date="2016-10-08",
            transactions=transactions,
        )

    def test_payment_return_import_pain_invalid(self):
        transactions = [
            {
                "returned_amount": 100.00,
                "reference": "E2EID1",
                "reason_add_info": "ACC NUMBER INVALID",
            },
        ]
        with self.assertRaises(UserError):
            self._test_return_import(
                "account_payment_return_import_iso20022",
                "test-sepa-pain-unpaid-invalid.xml",
                "MSGID99345678912",
                local_account="NL77ABNA0574908765",
                date="2016-10-08",
                transactions=transactions,
            )

    def test_zip_import_pain(self):
        """Test import of multiple statements from zip file."""
        self._test_return_import(
            "account_payment_return_import_iso20022",
            "test-sepa-pain-unpaid.zip",
            "MSGID99345678912",
            local_account="NL77ABNA0574908765",
            date="2016-10-08",
        )

    def test_payment_return_import_camt_053(self):
        """Test correct creation of single payment return."""
        transactions = [
            {
                "returned_amount": 100.00,
                "reference": "E2EID1",
                "reason_add_info": "/RTYP/RTRN",
            },
        ]
        self._test_return_import(
            "account_payment_return_import_iso20022",
            "test-sepa-camt-053-unpaid.xml",
            "ZY08XXXXXXIS634C",
            local_account="NL77ABNA0574908765",
            date="2016-10-08",
            transactions=transactions,
        )

    def test_payment_return_import_camt_054(self):
        """Test correct creation of single payment return."""
        transactions = [
            {
                "returned_amount": 100.00,
                "reference": "E2EID1",
                "reason_add_info": "/RTYP/RTRN",
            },
        ]
        self._test_return_import(
            "account_payment_return_import_iso20022",
            "test-sepa-camt-054-unpaid.xml",
            "ZY08XXXXXXIS634C",
            local_account="NL77ABNA0574908765",
            date="2016-10-08",
            transactions=transactions,
        )

    def test_payment_return_import_camt_invalid(self):
        transactions = [
            {
                "returned_amount": 100.00,
                "reference": "E2EID1",
                "reason_add_info": "/RTYP/RTRN",
            },
        ]
        with self.assertRaises(UserError):
            self._test_return_import(
                "account_payment_return_import_iso20022",
                "test-sepa-camt-unpaid-invalid.xml",
                "ZY08XXXXXXIS634C",
                local_account="NL77ABNA0574908765",
                date="2016-10-08",
                transactions=transactions,
            )

    def test_zip_import_camt(self):
        """Test import of multiple statements from zip file."""
        self._test_return_import(
            "account_payment_return_import_iso20022",
            "test-sepa-camt-unpaid.zip",
            "ZY08XXXXXXIS634C",
            local_account="NL77ABNA0574908765",
            date="2016-10-08",
        )
