# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from freezegun import freeze_time

from odoo.tests.common import Form

from .common import TestAccountFinancialDiscountCommon


@freeze_time("2019-05-01")
class TestAccountFinancialDiscountReconciliation(TestAccountFinancialDiscountCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.reconciliation_model = cls.env["account.reconcile.model"].search(
            [("rule_type", "=", "invoice_matching")], limit=1
        )
        cls.reconciliation_model.write(
            {
                "match_partner": False,
            }
        )

        cls.amount_taxed_without_discount = 1150.0
        cls.amount_taxed_discount = 23.0
        cls.amount_taxed_with_discount = 1127.0
        cls.amount_discount_tax = 3.0

        cls.amount_untaxed_without_discount = 1000.0
        cls.amount_untaxed_discount = 20.0
        cls.amount_untaxed_with_discount = 980.0

    def _create_bank_statement_line(self, date, label, amount, journal=None):
        if journal is None:
            journal = self.bank_journal
        statement_line_form = Form(
            self.env["account.bank.statement.line"].with_context(
                default_journal_id=journal.id
            )
        )
        statement_line_form.date = date
        statement_line_form.payment_ref = label
        statement_line_form.amount = amount
        return statement_line_form.save()

    def test_client_invoice_with_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
        )
        self.init_invoice_line(invoice, 1.0, self.amount_untaxed_without_discount)
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        st_line = self._create_bank_statement_line(
            "2019-05-20", invoice.name, self.amount_taxed_with_discount
        )
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertFalse(matching_amls)
        invoice.force_early_discount = True
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertDictEqual(
            matching_amls,
            {
                "auto_reconcile": True,
                "amls": invoice_receivable_line,
                "model": self.reconciliation_model,
            },
        )

    def test_client_invoice_without_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
        )
        self.init_invoice_line(
            invoice, 1.0, self.amount_untaxed_without_discount, with_tax=False
        )
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        st_line = self._create_bank_statement_line(
            "2019-05-20", invoice.name, self.amount_untaxed_with_discount
        )
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertFalse(matching_amls)
        invoice.force_early_discount = True
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertDictEqual(
            matching_amls,
            {
                "auto_reconcile": True,
                "amls": invoice_receivable_line,
                "model": self.reconciliation_model,
            },
        )

    def test_vendor_bill_with_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(vendor_bill, 1.0, self.amount_untaxed_without_discount)
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        st_line = self._create_bank_statement_line(
            "2019-05-20",
            vendor_bill.payment_reference,
            -self.amount_taxed_with_discount,
        )
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertFalse(matching_amls)
        vendor_bill.force_early_discount = True
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertDictEqual(
            matching_amls,
            {
                "auto_reconcile": True,
                "amls": vendor_bill_payable_line,
                "model": self.reconciliation_model,
            },
        )

    def test_vendor_bill_without_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(
            vendor_bill,
            1.0,
            self.amount_untaxed_without_discount,
            with_tax=False,
        )
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        st_line = self._create_bank_statement_line(
            "2019-05-20",
            vendor_bill.payment_reference,
            -self.amount_untaxed_with_discount,
        )
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertFalse(matching_amls)
        vendor_bill.force_early_discount = True
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertDictEqual(
            matching_amls,
            {
                "auto_reconcile": True,
                "amls": vendor_bill_payable_line,
                "model": self.reconciliation_model,
            },
        )

    def test_client_invoice_eur_with_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice, 1.0, self.amount_untaxed_without_discount)
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        st_line = self._create_bank_statement_line(
            "2019-05-20",
            invoice.name,
            self.amount_taxed_with_discount,
            journal=self.eur_bank_journal,
        )
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertFalse(matching_amls)
        invoice.force_early_discount = True
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertDictEqual(
            matching_amls,
            {
                "auto_reconcile": True,
                "amls": invoice_receivable_line,
                "model": self.reconciliation_model,
            },
        )

    def test_vendor_bill_eur_with_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            currency=self.eur_currency,
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(vendor_bill, 1.0, self.amount_untaxed_without_discount)
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        st_line = self._create_bank_statement_line(
            "2019-05-20",
            vendor_bill.payment_reference,
            -self.amount_taxed_with_discount,
            journal=self.eur_bank_journal,
        )
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertFalse(matching_amls)
        vendor_bill.force_early_discount = True
        matching_amls = self.reconciliation_model._apply_rules(st_line, None)
        self.assertDictEqual(
            matching_amls,
            {
                "auto_reconcile": True,
                "amls": vendor_bill_payable_line,
                "model": self.reconciliation_model,
            },
        )
