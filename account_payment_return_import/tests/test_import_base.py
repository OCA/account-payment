# Copyright 2017 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import Form

from .test_import_file import TestPaymentReturnFile


class TestImportBase(TestPaymentReturnFile):
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
                "company_id": cls.company.id,
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
        cls.journal_sale = cls.env["account.journal"].create(
            {"name": "Test Sale Journal", "code": "SALE", "type": "sale"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.reason = cls.env["payment.return.reason"].create(
            {"code": "RTEST", "name": "Reason Test"}
        )
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test account",
                "code": "TEST",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        cls.account_income = cls.env["account.account"].create(
            {
                "name": "Test income account",
                "code": "INCOME",
                "account_type": "income_other",
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "journal_id": cls.journal_sale.id,
                "company_id": cls.env.user.company_id.id,
                "currency_id": cls.env.user.company_id.currency_id.id,
                "partner_id": cls.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": cls.account_income.id,
                            "name": "Test line",
                            "price_unit": 250.9,
                            "quantity": 1,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )
        cls.invoice.action_post()
        cls.receivable_line = cls.invoice.line_ids.filtered(
            lambda x: x.account_id.account_type == "asset_receivable"
        )
        # Create payment from invoice
        cls.payment_register_model = cls.env["account.payment.register"]
        payment_register = Form(
            cls.payment_register_model.with_context(
                active_model="account.move", active_ids=cls.invoice.ids
            )
        )
        cls.payment = payment_register.save()._create_payments()
        cls.payment_move = cls.payment.move_id

    def test_payment_return_import(self):
        self._test_return_import(
            "account_payment_return_import",
            "test_payment_import.csv",
            "M00000123",
            local_account="NL77ABNA0574908765",
        )

    def test_zipped_payment_return_import(self):
        self._test_return_import(
            "account_payment_return_import",
            "test_payment_import.zip",
            "M00000123",
            local_account="NL77ABNA0574908765",
        )

    def test_payment_return_import_empty(self):
        with self.assertRaises(UserError):
            self._test_return_import(
                "account_payment_return_import",
                "test_empty.csv",
                "TEST123456",
                local_account="NL77ABNA0574908765",
            )

    def test_zip_import_empty(self):
        with self.assertRaises(UserError):
            self._test_return_import(
                "account_payment_return_import",
                "test_zipped_payment_import_empty.zip",
                "TEST123456",
                local_account="NL77ABNA0574908765",
            )
