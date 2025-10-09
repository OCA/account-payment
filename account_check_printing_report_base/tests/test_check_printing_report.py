# Copyright 2016 ForgeFlow, S.L.
# Copyright 2018 iterativo.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time

from odoo import fields
from odoo.exceptions import RedirectWarning
from odoo.tests.common import TransactionCase


class TestAccountCheckPrintingReportBase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.langs = ("en_US", "es_ES")
        self.rl = self.env["res.lang"]
        for lang in self.langs:
            if not self.rl.search([("code", "=", lang)]):
                self.rl._activate_lang(lang)
        self.account_invoice_model = self.env["account.move"]
        self.journal_model = self.env["account.journal"]
        self.payment_method_model = self.env["account.payment.method"]
        self.payment_method_line_model = self.env["account.payment.method.line"]
        self.account_account_model = self.env["account.account"]
        self.payment_model = self.env["account.payment"]
        self.report = self.env[
            "report.account_check_printing_report_base.report_check_base"
        ]

        self.partner1 = self.env.ref("base.res_partner_1")
        self.company = self.env.ref("base.main_company")
        self.currency_usd_id = self.env.ref("base.USD").id
        self.currency_euro_id = self.env.ref("base.EUR").id
        self.product = self.env.ref("product.product_product_4")
        self.check_report = (
            "account_check_printing_report_base.action_report_check_base"
        )
        self.check_report_a4 = (
            "account_check_printing_report_base.action_report_check_base_a4"
        )
        self.action_check_report = self.env.ref(
            "account_check_printing_report_base.action_report_check_base"
        )
        self.payment_method_check = self.payment_method_model.search(
            [("code", "=", "check_printing")],
            limit=1,
        )
        if not self.payment_method_check:
            self.payment_method_check = self.payment_method_model.create(
                {
                    "name": "Check",
                    "code": "check_printing",
                    "payment_type": "outbound",
                    "check": True,
                }
            )
        self.purchase_journal = self.journal_model.create(
            {"name": "Purchase Journal - Test", "type": "purchase", "code": "Test"}
        )
        self.bank_journal = self.journal_model.create(
            {
                "name": "Cash Journal - Test",
                "type": "bank",
                "code": "bank",
                "check_manual_sequencing": True,
            }
        )
        self.payment_method_line_check = self.payment_method_line_model.create(
            {
                "name": "Check",
                "payment_method_id": self.payment_method_check.id,
                "journal_id": self.bank_journal.id,
            }
        )
        self.acc_payable = self._create_account(
            "account payable test", "ACPRB1", "liability_payable", True
        )
        self.vendor_bill = self._create_vendor_bill(self.acc_payable)
        self.vendor_bill.invoice_date = time.strftime("%Y") + "-07-15"
        self.acc_expense = self._create_account(
            "account expense test", "ACPRB2", "expense", False
        )
        self._create_invoice_line(self.acc_expense, self.vendor_bill)

        self.vendor_bill.action_post()
        # Pay the invoice using a bank journal associated to the main company
        ctx = {"active_model": "account.move", "active_ids": [self.vendor_bill.id]}
        register_payments = self.payment_model.with_context(**ctx).create(
            {
                "date": time.strftime("%Y") + "-07-15",
                "journal_id": self.bank_journal.id,
                "payment_method_line_id": self.payment_method_line_check.id,
            }
        )
        register_payments.action_post()
        self.payment = self.payment_model.search([], order="id desc", limit=1)

    def _create_account(self, name, code, account_type, reconcile):
        account = self.account_account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": account_type,
                "reconcile": reconcile,
            }
        )
        return account

    def _create_vendor_bill(self, account):
        vendor_bill = self.account_invoice_model.create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner1.id,
                "currency_id": self.company.currency_id.id,
                "journal_id": self.purchase_journal.id,
                "company_id": self.company.id,
            }
        )
        return vendor_bill

    def _create_invoice_line(self, account, invoice):
        invoice = invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test invoice line",
                            "account_id": account.id,
                            "quantity": 1.000,
                            "price_unit": 2.99,
                            "product_id": self.product.id,
                        },
                    )
                ]
            }
        )

        return invoice

    def test_01_check_printing_no_layout(self):
        """Test if the exception raises when no layout is set for a
        company or for the journal."""
        with self.assertRaises(RedirectWarning):
            self.payment.do_print_checks()

        # Set check layout verification by journal
        ICPSudo = self.env["ir.config_parameter"].sudo()
        ICPSudo.set_param(
            "account_check_printing_report_base.check_layout_verification", "by_journal"
        )
        self.assertFalse(self.payment.journal_id.bank_check_printing_layout)
        with self.assertRaises(RedirectWarning):
            self.payment.do_print_checks()
        content = self.env["ir.actions.report"]._render_qweb_pdf(
            self.action_check_report.xml_id, res_ids=self.payment.ids
        )
        self.assertEqual(content[1], "html")

    def test_02_check_printing_with_layout(self):
        """Test if the check is printed when the layout is specified for a
        company and journal."""

        self.company.account_check_printing_layout = self.check_report
        self.payment.journal_id.bank_check_printing_layout = self.check_report_a4
        e = False
        try:
            self.payment.do_print_checks()
        except RedirectWarning as e:
            e = e.name
        self.assertEqual(e, False)
        content = self.env["ir.actions.report"]._render_qweb_pdf(
            self.action_check_report.xml_id, res_ids=self.payment.ids
        )
        self.assertEqual(content[1], "html")

    def test_03_fotmat_form(self):
        """Test formatting on check form"""
        # Convert date to formatting from partner : 2020-01-20 > 01/20/2020
        today = fields.Date.today()
        date = self.report._format_date_to_partner_lang(today, self.partner1.id)
        self.assertEqual(date, today.strftime("%m/%d/%Y"))
        # Fill starts in amount
        amount = 100.0
        amount_in_word = "One Hundred Euro"
        stars = 100 - len(amount_in_word)
        amount1 = self.report.fill_stars_number(str(amount))
        amount2 = self.report.fill_stars(amount_in_word)
        self.assertEqual(amount1, f"***** {amount} *")
        self.assertEqual(amount2, "{} {}".format(amount_in_word, ("*" * stars)))

    def test_num2words(self):
        report_model = "report.account_check_printing_report_base.promissory_footer_a4"
        words_number = (
            self.env[report_model].with_context(lang="en_US").amount2words(4.9)
        )
        self.assertEqual(words_number, "four euro, ninety cents")
        words_number = (
            self.env[report_model].with_context(lang="es_ES").amount2words(4.9)
        )
        self.assertEqual(words_number, "cuatro euros con noventa céntimos")
        words_number = (
            self.env[report_model].with_context(lang="es_ES").amount2words(4.95)
        )
        self.assertEqual(words_number, "cuatro euros con noventa y cinco céntimos")
