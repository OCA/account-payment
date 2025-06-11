# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from freezegun import freeze_time

from odoo.tests.common import Form

from .common import TestAccountFinancialDiscountCommon


@freeze_time("2019-04-01")
class TestAccountFinancialDiscountManualPayment(TestAccountFinancialDiscountCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice1 = cls.init_invoice(
            cls.partner,
            "in_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.invoice1, 1.0, 1000.0)

        cls.invoice2 = cls.init_invoice(
            cls.partner,
            "in_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
        )
        cls.init_invoice_line(cls.invoice2, 1.0, 1000.0)

        cls.invoice3 = cls.init_invoice(
            cls.partner,
            "in_invoice",
            payment_term=cls.payment_thirty_net,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.invoice3, 1.0, 1000.0)

        cls.client_invoice1 = cls.init_invoice(
            cls.customer,
            "out_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.client_invoice1, 1.0, 1000.0)

        cls.client_invoice2 = cls.init_invoice(
            cls.customer,
            "out_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
        )
        cls.init_invoice_line(cls.client_invoice2, 1.0, 1000.0)

        cls.client_invoice3 = cls.init_invoice(
            cls.customer,
            "out_invoice",
            payment_term=cls.payment_thirty_net,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.client_invoice3, 1.0, 1000.0)

        cls.amount_without_discount = 1150.0
        cls.amount_discount = 23.0
        cls.amount_with_discount = 1127.0

    def _assert_payment_line_with_discount_from_invoice(self, invoice):
        invoice_payment_line = self._get_payment_lines(invoice)
        # The payment move line must have full amount to set invoice as paid
        self.assertEqual(
            invoice_payment_line.amount_currency, self.amount_without_discount
        )
        invoice_payment = invoice_payment_line.mapped("payment_id")
        # # The payment must have the amount with discount
        self.assertEqual(invoice_payment.amount, self.amount_with_discount)

    def test_single_invoice_payment_with_discount_late(self):
        """Test register payment for a vendor bill with late discount"""
        self.invoice2.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice2.ids,
                active_id=self.invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_early_discount, True)
        self.assertEqual(payment_wizard_form.force_early_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard_form.force_early_discount = True
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))

    def test_single_invoice_payment_with_discount_late_forced(self):
        """Test register payment for a vendor bill with late discount forced"""
        self.invoice2.action_post()
        self.invoice2.force_early_discount = True
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice2.ids,
                active_id=self.invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_early_discount, True)
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))

    def test_single_invoice_payment_without_discount(self):
        """Test register payment for a vendor bill without discount"""
        self.invoice3.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice3.ids,
                active_id=self.invoice3.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_early_discount, False)
        self.assertEqual(payment_wizard_form.force_early_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.invoice3.payment_state, ("paid", "in_payment"))

    @classmethod
    def _get_payment_lines(cls, invoice):
        """Returns payment lines match with the invoice"""
        # Inspired by account.move._get_reconciled_info_JSON_values
        invoice_term_lines = invoice.line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        )
        invoice_matched_lines = invoice_term_lines.mapped(
            "matched_debit_ids"
        ) | invoice_term_lines.mapped("matched_credit_ids")
        invoice_counterpart_lines = invoice_matched_lines.mapped(
            "debit_move_id"
        ) | invoice_matched_lines.mapped("debit_move_id")
        return invoice_counterpart_lines.filtered(
            lambda line: line not in invoice.line_ids
        )

    def test_multi_invoice_payment_with_discount_late(self):
        """Test register payment for multiple vendor bills with late discount"""
        invoice4 = self.invoice2.copy({"invoice_date": self.invoice2.invoice_date})
        invoices = self.invoice2 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_early_discount)
        self.assertFalse(payment_wizard_form.force_early_discount)
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        invoice2_payment_line = self._get_payment_lines(self.invoice2)
        invoice2_payment = invoice2_payment_line.mapped("payment_id")
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))
        invoice4_payment_lines = self._get_payment_lines(invoice4)
        invoice4_payment = invoice4_payment_lines.mapped("payment_id")
        self.assertEqual(invoice4_payment.amount, self.amount_without_discount)
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_payment_with_discount_late_forced(self):
        """Test register payment for multiple vendor bills with late discount forced
        at invoice level"""
        invoice4 = self.invoice2.copy({"invoice_date": self.invoice2.invoice_date})
        invoice4.force_early_discount = True
        invoices = self.invoice2 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_early_discount)
        self.assertFalse(payment_wizard_form.force_early_discount)
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        invoice2_payment_lines = self._get_payment_lines(self.invoice2)
        invoice2_payment = invoice2_payment_lines.mapped("payment_id")
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice4)
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_payment_with_discount_late_forced_wizard(self):
        """Test register payment grouped for multiple vendor bills with late discount
        forced at wizard level"""
        invoice4 = self.invoice2.copy({"invoice_date": self.invoice2.invoice_date})
        invoice4.force_early_discount = True
        invoices = self.invoice2 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_early_discount)
        self.assertFalse(payment_wizard_form.force_early_discount)
        payment_wizard_form.force_early_discount = True
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(self.invoice2)
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice4)
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_late(self):
        """Test register payment for multiple vendor bills with force discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_early_discount)
        self.assertFalse(payment_wizard_form.force_early_discount)
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        invoice2_payment_line = self._get_payment_lines(invoice2)
        invoice2_payment = invoice2_payment_line.mapped("payment_id")
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_late_forced(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        invoice2.force_early_discount = True
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_early_discount)
        self.assertFalse(payment_wizard_form.force_early_discount)
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_late_forced_wizard(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_early_discount)
        self.assertFalse(payment_wizard_form.force_early_discount)
        payment_wizard_form.force_early_discount = True
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_customer_manual_payment_with_discount_late(self):
        """Test register payment for a customer invoice with late discount"""
        self.client_invoice2.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.client_invoice2.ids,
                active_id=self.client_invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_early_discount, True)
        self.assertEqual(payment_wizard_form.force_early_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard_form.force_early_discount = True
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.client_invoice2.payment_state, ("paid", "in_payment"))

    def test_customer_manual_payment_with_discount_late_forced(self):
        """Test register payment for a customer invoice with late discount forced"""
        self.client_invoice2.action_post()
        self.client_invoice2.force_early_discount = True
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.client_invoice2.ids,
                active_id=self.client_invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_early_discount, True)
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.client_invoice2.payment_state, ("paid", "in_payment"))

    def test_customer_manual_payment_without_discount(self):
        """Test register payment for a customer invoice without discount"""
        self.client_invoice3.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.client_invoice3.ids,
                active_id=self.client_invoice3.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_early_discount, False)
        self.assertEqual(payment_wizard_form.force_early_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.client_invoice3.payment_state, ("paid", "in_payment"))
