# © 2016 Eficent Business and IT Consulting Services S.L.
# Copyright 2018 iterativo.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time

from odoo import fields
from odoo.exceptions import RedirectWarning
from odoo.tests.common import TransactionCase


class TestAccountCheckPrintingReportBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.langs = ("en_US", "es_ES")
        cls.rl = cls.env["res.lang"]
        for lang in cls.langs:
            if not cls.rl.search([("code", "=", lang)]):
                cls.rl.load_lang(lang)
        cls.account_invoice_model = cls.env["account.move"]
        cls.journal_model = cls.env["account.journal"]
        cls.payment_method_model = cls.env["account.payment.method"]
        cls.payment_method_line_model = cls.env["account.payment.method.line"]
        cls.account_account_model = cls.env["account.account"]
        cls.payment_model = cls.env["account.payment"]
        cls.report = cls.env[
            "report.account_check_printing_report_base.report_check_base"
        ]

        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.company = cls.env.ref("base.main_company")
        cls.currency_usd_id = cls.env.ref("base.USD").id
        cls.currency_euro_id = cls.env.ref("base.EUR").id
        cls.acc_payable = "liability_payable"
        cls.acc_expense = "expense"
        cls.product = cls.env.ref("product.product_product_4")
        cls.check_report = "account_check_printing_report_base.action_report_check_base"
        cls.check_report_a4 = (
            "account_check_printing_report_base.action_report_check_base_a4"
        )
        cls.action_check_report = (
            "account_check_printing_report_base.action_report_check_base"
        )
        cls.payment_method_check = cls.payment_method_model.search(
            [("code", "=", "check_printing")],
            limit=1,
        )
        if not cls.payment_method_check:
            cls.payment_method_check = cls.payment_method_model.create(
                {
                    "name": "Check",
                    "code": "check_printing",
                    "payment_type": "outbound",
                    "check": True,
                }
            )
        cls.purchase_journal = cls.journal_model.create(
            {"name": "Purchase Journal - Test", "type": "purchase", "code": "Test"}
        )
        cls.bank_journal = cls.journal_model.create(
            {
                "name": "Cash Journal - Test",
                "type": "bank",
                "code": "bank",
                "check_manual_sequencing": True,
            }
        )
        cls.payment_method_line_check = cls.payment_method_line_model.create(
            {
                "name": "Check",
                "payment_method_id": cls.payment_method_check.id,
                "journal_id": cls.bank_journal.id,
            }
        )
        cls.acc_payable = cls._create_account(
            "account payable test", "ACPRB1", cls.acc_payable, True
        )
        cls.vendor_bill = cls._create_vendor_bill(cls.acc_payable)
        cls.vendor_bill.invoice_date = time.strftime("%Y") + "-07-15"
        cls.acc_expense = cls._create_account(
            "account expense test", "ACPRB2", cls.acc_expense, False
        )
        cls._create_invoice_line(cls.acc_expense, cls.vendor_bill)

        cls.vendor_bill.action_post()
        # Pay the invoice using a bank journal associated to the main company
        ctx = {"active_model": "account.move", "active_ids": [cls.vendor_bill.id]}
        register_payments = cls.payment_model.with_context(**ctx).create(
            {
                "date": time.strftime("%Y") + "-07-15",
                "journal_id": cls.bank_journal.id,
                "payment_method_line_id": cls.payment_method_line_check.id,
            }
        )
        register_payments.action_post()
        cls.payment = cls.payment_model.search([], order="id desc", limit=1)

    @classmethod
    def _create_account(cls, name, code, user_type, reconcile):
        account = cls.account_account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": user_type,
                "company_id": cls.company.id,
                "reconcile": reconcile,
            }
        )
        return account

    @classmethod
    def _create_vendor_bill(cls, account):
        vendor_bill = cls.account_invoice_model.create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.partner1.id,
                "currency_id": cls.company.currency_id.id,
                "journal_id": cls.purchase_journal.id,
                "company_id": cls.company.id,
            }
        )
        return vendor_bill

    @classmethod
    def _create_invoice_line(cls, account, invoice):
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
                            "product_id": cls.product.id,
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
        self.assertFalse(self.payment.journal_id.account_check_printing_layout)
        with self.assertRaises(RedirectWarning):
            self.payment.do_print_checks()
        content = self.env["ir.actions.report"]._render_qweb_pdf(
            self.action_check_report, res_ids=self.payment.ids
        )
        self.assertEqual(content[1], "html")

    def test_02_check_printing_with_layout(self):
        """Test if the check is printed when the layout is specified for a
        company and journal."""

        self.company.account_check_printing_layout = self.check_report
        self.payment.journal_id.account_check_printing_layout = self.check_report_a4
        e = False
        try:
            self.payment.do_print_checks()
        except RedirectWarning as e:
            e = e.name
        self.assertEqual(e, False)

        content = self.env["ir.actions.report"]._render_qweb_pdf(
            self.action_check_report, res_ids=self.payment.ids
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
        self.assertEqual(amount1, "***** %s *" % amount)
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
