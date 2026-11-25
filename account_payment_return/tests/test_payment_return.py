# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2017 Tecnativa - Luis M. Ontalba
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestPaymentReturn(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test Sales Journal", "code": "tVEN", "type": "sale"}
        )
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test account",
                "code": "TEST",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        cls.transfer_account = cls.env["account.account"].create(
            {
                "name": "Test transfer account",
                "code": "TESTTR",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        cls.env.company.transfer_account_id = cls.transfer_account
        cls.partner_expense = cls.env["res.partner"].create({"name": "PE"})
        cls.bank_journal = cls.env["account.journal"].create(
            {
                "name": "Test Bank Journal",
                "code": "BANKTEST",
                "type": "bank",
                "default_expense_account_id": cls.account.id,
                "default_expense_partner_id": cls.partner_expense.id,
            }
        )
        cls.account_income = cls.env["account.account"].create(
            {
                "name": "Test income account",
                "code": "INCOME",
                "account_type": "income_other",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "journal_id": cls.journal.id,
                "company_id": cls.env.user.company_id.id,
                "currency_id": cls.env.user.company_id.currency_id.id,
                "partner_id": cls.partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "account_id": cls.account_income.id,
                            "name": "Test line",
                            "price_unit": 50,
                            "quantity": 10,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )
        cls.reason = cls.env["payment.return.reason"].create(
            {"code": "RTEST", "name": "Reason Test"}
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
        cls.payment_line = cls.payment_move.line_ids.filtered(
            lambda x: x.account_id.account_type == "asset_receivable"
        )
        # Create payment return
        cls.payment_return = cls.env["payment.return"].create(
            {
                "journal_id": cls.bank_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "partner_id": cls.partner.id,
                            "move_line_ids": [(6, 0, cls.payment_line.ids)],
                            "amount": cls.payment_line.credit,
                            "expense_account": cls.account.id,
                            "expense_amount": 10.0,
                            "expense_partner_id": cls.partner.id,
                        },
                    )
                ],
            }
        )

    def test_confirm_error(self):
        self.payment_return.line_ids[0].move_line_ids = False
        with self.assertRaises(UserError):
            self.payment_return.action_confirm()

    def test_onchange_move_line(self):
        record = self.env["payment.return.line"].new()
        record.move_line_ids = self.payment_line.ids
        record._onchange_move_line()
        self.assertEqual(record.amount, self.payment_line.credit)

    def test_payment_return(self):
        self.payment_return.action_cancel()  # No effect
        self.assertEqual(self.invoice.payment_state, "paid")
        self.assertEqual(self.payment_return.state, "cancelled")
        self.payment_return.action_draft()
        self.assertEqual(self.payment_return.state, "draft")
        self.payment_return.line_ids[0].expense_amount = 10.0
        self.payment_return.line_ids[0]._onchange_expense_amount()
        self.payment_return.action_confirm()
        self.assertEqual(self.payment_return.state, "done")
        self.assertEqual(self.payment_return.move_id.state, "posted")
        self.assertAlmostEqual(
            sum(self.payment_return.move_id.line_ids.mapped("debit")),
            sum(self.payment_return.move_id.line_ids.mapped("credit")),
        )
        self.assertEqual(self.invoice.payment_state, "not_paid")
        self.assertEqual(self.invoice.amount_residual, self.receivable_line.debit)
        self.assertEqual(
            sum(
                self.payment_return.move_id.line_ids.filtered(
                    lambda line: line.debit == 10.0
                ).mapped("debit")
            ),
            10.0,
        )
        self.assertFalse(self.receivable_line.reconciled)
        self.assertEqual(
            self.payment_return.line_ids[0].expense_account,
            self.bank_journal.default_expense_account_id,
        )
        self.assertEqual(
            self.payment_return.line_ids[0].expense_partner_id,
            self.bank_journal.default_expense_partner_id,
        )
        self.assertEqual(len(self.payment_return.move_id.line_ids), 4)
        with self.assertRaises(UserError):
            self.payment_return.unlink()
        self.payment_return.action_cancel()
        self.assertEqual(self.payment_return.state, "cancelled")
        self.assertEqual(self.invoice.payment_state, "paid")
        self.assertTrue(self.receivable_line.reconciled)
        self.payment_return.action_draft()
        self.assertEqual(self.payment_return.state, "draft")
        self.payment_return.unlink()

    def test_payment_partial_return(self):
        self.payment_return.line_ids[0].amount = 200.0
        self.assertEqual(self.invoice.payment_state, "paid")
        self.payment_return.action_confirm()
        self.assertEqual(self.invoice.payment_state, "partial")
        self.assertEqual(self.invoice.amount_residual, 200.0)
        self.assertFalse(self.receivable_line.reconciled)
        widget = self.invoice.invoice_payments_widget
        self.assertEqual(len(widget["content"]), 3)
        current_payment = [row for row in widget["content"] if not row.get("returned")]
        returned_payment = [row for row in widget["content"] if row.get("returned")]
        self.assertEqual(len(current_payment), 2)
        self.assertEqual(len(returned_payment), 1)
        self.assertEqual(returned_payment[0]["amount"], -200.0)
        self.assertIsInstance(returned_payment[0]["currency_id"], int)
        self.assertIsInstance(returned_payment[0]["partial_id"], int)
        self.assertTrue(
            self.env["account.partial.reconcile"]
            .browse(returned_payment[0]["partial_id"])
            .exists()
        )
        self.assertIsInstance(returned_payment[0]["amount_company_currency"], str)
        returned_history_payment = next(
            row
            for row in current_payment
            if row["partial_id"] == returned_payment[0]["partial_id"]
        )
        self.assertEqual(
            returned_history_payment["amount_company_currency"],
            returned_payment[0]["amount_company_currency"],
        )
        self.assertIn("exchange_info", widget)
        self.payment_return.action_cancel()
        self.assertEqual(self.invoice.payment_state, "paid")
        self.assertEqual(self.invoice.amount_residual, 0.0)
        self.assertTrue(self.receivable_line.reconciled)

    def test_multiple_payments_keep_reconciled_and_returned_history(self):
        invoice = self.invoice.copy()
        invoice.action_post()

        payments = []
        for amount in (300.0, 200.0):
            payment_register = Form(
                self.env["account.payment.register"].with_context(
                    active_model="account.move", active_ids=invoice.ids
                )
            )
            payment_register.amount = amount
            payments.append(payment_register.save()._create_payments())

        returned_payment_line = payments[1].move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        payment_return = self.env["payment.return"].create(
            {
                "journal_id": self.bank_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "partner_id": self.partner.id,
                            "move_line_ids": [Command.set(returned_payment_line.ids)],
                            "amount": returned_payment_line.credit,
                        }
                    )
                ],
            }
        )
        payment_return.action_confirm()

        self.assertEqual(invoice.amount_residual, 200.0)
        widget = invoice.invoice_payments_widget
        self.assertEqual(len(widget["content"]), 3)
        self.assertEqual(sum(row["amount"] for row in widget["content"]), 300.0)
        self.assertEqual(
            len([row for row in widget["content"] if row.get("returned")]), 1
        )

    def test_foreign_currency_return_keeps_widget_currency_and_exchange_info(self):
        currency = self.env.ref("base.USD")
        if currency == self.env.company.currency_id:
            currency = self.env.ref("base.EUR")
        currency.active = True
        self.env["res.currency.rate"].create(
            {
                "name": "2026-01-01",
                "rate": 1.25,
                "currency_id": currency.id,
                "company_id": self.env.company.id,
            }
        )
        invoice = self.invoice.copy(
            {"currency_id": currency.id, "invoice_date": "2026-01-01"}
        )
        invoice.action_post()
        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids
            )
        )
        payment = payment_register.save()._create_payments()
        payment_line = payment.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        payment_return = self.env["payment.return"].create(
            {
                "journal_id": self.bank_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "partner_id": self.partner.id,
                            "move_line_ids": [Command.set(payment_line.ids)],
                            "amount": payment_line.credit * 0.4,
                        }
                    )
                ],
            }
        )
        payment_return.action_confirm()

        self.assertAlmostEqual(invoice.amount_residual, 200.0)
        widget = invoice.invoice_payments_widget
        self.assertIn("exchange_info", widget)
        returned_row = next(row for row in widget["content"] if row.get("returned"))
        current_rows = [row for row in widget["content"] if not row.get("returned")]
        self.assertEqual(len(current_rows), 2)
        self.assertAlmostEqual(sum(row["amount"] for row in current_rows), 500.0)
        self.assertAlmostEqual(returned_row["amount"], -200.0)
        self.assertEqual(returned_row["currency_id"], currency.id)
        self.assertTrue(
            any(isinstance(row["amount_foreign_currency"], str) for row in current_rows)
        )

    def test_company_access_is_limited_to_active_companies(self):
        company_a = self.env.company
        company_b = self.env["res.company"].create({"name": "Other company"})
        journal_b = self.env["account.journal"].create(
            {
                "name": "Other company bank",
                "code": "BANKB",
                "type": "bank",
                "company_id": company_b.id,
            }
        )
        payment_return_b = self.env["payment.return"].create(
            {"company_id": company_b.id, "journal_id": journal_b.id}
        )
        payment_return_line_b = self.env["payment.return.line"].create(
            {"return_id": payment_return_b.id}
        )
        accounting_user = self.env["res.users"].create(
            {
                "name": "Company A accountant",
                "login": "company-a-accountant",
                "company_id": company_a.id,
                "company_ids": [Command.set(company_a.ids)],
                "group_ids": [
                    Command.set([self.env.ref("account.group_account_invoice").id])
                ],
            }
        )
        context = {"allowed_company_ids": company_a.ids}

        visible_returns = (
            self.env["payment.return"]
            .with_user(accounting_user)
            .with_context(**context)
        )
        visible_return_lines = (
            self.env["payment.return.line"]
            .with_user(accounting_user)
            .with_context(**context)
        )
        self.assertNotIn(payment_return_b, visible_returns.search([]))
        self.assertNotIn(payment_return_line_b, visible_return_lines.search([]))

    def test_find_match_ref_from_invoice(self):
        self.payment_return.line_ids.write(
            {
                "partner_id": False,
                "move_line_ids": [(6, 0, [])],
                "amount": 0.0,
                "reference": self.invoice.name,
            }
        )
        self.payment_return.button_match()
        self.assertAlmostEqual(
            self.payment_return.line_ids[0].amount, self.payment_line.credit
        )
        self.assertEqual(self.payment_return.line_ids.move_line_ids, self.payment_line)

    def test_matching_searches_do_not_write(self):
        line = self.payment_return.line_ids
        line.write(
            {
                "partner_id": False,
                "move_line_ids": [Command.clear()],
                "amount": 0.0,
                "concept": False,
                "reference": self.invoice.name,
            }
        )
        self.assertEqual(line._get_matching_move_lines(), self.payment_line)
        self.payment_move.ref = "Unique payment reference"
        line.reference = self.payment_move.ref
        self.assertEqual(line._get_matching_move_lines(), self.payment_line)

        self.payment_move.payment_reference = "External bank reference"
        line.reference = self.payment_move.payment_reference
        self.assertEqual(line._get_matching_move_lines(), self.payment_line)

        self.payment_line.remove_move_reconcile()
        self.assertEqual(line._get_matching_move_lines(), self.payment_line)
        self.assertFalse(line.move_line_ids)
        self.assertFalse(line.partner_id)
        self.assertFalse(line.concept)
        self.assertEqual(line.amount, 0.0)

    def test_matching_does_not_fall_back_to_document_or_line_names(self):
        line = self.payment_return.line_ids
        self.payment_move.write({"ref": False, "payment_reference": False})
        self.payment_line.name = "Name-only payment line"
        for reference in (
            self.invoice.name,
            self.payment_move.name,
            self.payment_line.name,
        ):
            line.reference = reference
            self.assertFalse(line._get_matching_move_lines())

    def test_matching_preserves_entered_amount_and_concept(self):
        line = self.payment_return.line_ids
        line.write(
            {
                "move_line_ids": [Command.clear()],
                "reference": self.invoice.name,
                "amount": 200.0,
                "concept": "Partial return entered manually",
            }
        )
        self.payment_return.button_match()
        self.assertEqual(line.move_line_ids, self.payment_line)
        self.assertEqual(line.amount, 200.0)
        self.assertEqual(line.concept, "Partial return entered manually")

    def test_matching_split_payments_uses_unique_references(self):
        invoice = self.invoice.copy()
        invoice.action_post()
        payments = self.env["account.payment"]
        for amount in (300.0, 200.0):
            register = Form(
                self.env["account.payment.register"].with_context(
                    active_model="account.move", active_ids=invoice.ids
                )
            )
            register.amount = amount
            payments |= register.save()._create_payments()
        for index, payment in enumerate(payments):
            payment.move_id.ref = f"{invoice.name}-{index}" if index else invoice.name
        payment_lines = payments.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        payment_return = self.env["payment.return"].create(
            {
                "journal_id": self.bank_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "reference": payment_line.ref,
                            "amount": payment_line.credit,
                        }
                    )
                    for payment_line in payment_lines
                ],
            }
        )
        payment_return.button_match()
        for return_line, payment_line in zip(
            payment_return.line_ids, payment_lines, strict=True
        ):
            self.assertEqual(return_line.move_line_ids, payment_line)
            self.assertEqual(return_line.partner_id, self.partner)

        # A shared reference cannot identify which of its payments to return.
        for payment in payments:
            payment.move_id.ref = invoice.name
        payment_return.line_ids.write(
            {"move_line_ids": [Command.clear()], "reference": invoice.name}
        )
        with self.assertRaisesRegex(UserError, "matches several payment lines"):
            payment_return.button_match()
        self.assertFalse(payment_return.line_ids.move_line_ids)

    def test_matching_excludes_other_company_payments(self):
        company = self.env["res.company"].create({"name": "Matching company B"})
        journal = self.env["account.journal"].create(
            {
                "name": "Matching journal B",
                "code": "MATCHB",
                "type": "general",
                "company_id": company.id,
            }
        )
        payment_return = self.env["payment.return"].create(
            {
                "company_id": company.id,
                "journal_id": journal.id,
                "line_ids": [Command.create({"reference": self.payment_move.ref})],
            }
        )
        self.assertFalse(payment_return.line_ids._get_matching_move_lines())

    def test_matching_skips_validation_without_pending_lines(self):
        self.env["payment.return.line"].create(
            {
                "return_id": self.payment_return.id,
                "partner_id": self.partner.id,
                "move_line_ids": [Command.set(self.payment_line.ids)],
            }
        )
        self.assertFalse(self.payment_return._get_lines_to_match())
        with patch.object(
            type(self.payment_return), "_check_duplicate_move_line"
        ) as check_duplicates:
            self.payment_return.button_match()
        check_duplicates.assert_not_called()

    def test_matching_domain_supports_outgoing_payments(self):
        payable = self.env["account.account"].create(
            {
                "name": "Matching payable",
                "code": "MATCHPAY",
                "account_type": "liability_payable",
                "reconcile": True,
            }
        )
        payment_move = self.env["account.move"].create(
            {
                "journal_id": self.bank_journal.id,
                "ref": "Supplier payment reference",
                "payment_reference": "Supplier bank reference",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": payable.id,
                            "partner_id": self.partner.id,
                            "debit": 500.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.bank_journal.default_account_id.id,
                            "credit": 500.0,
                        }
                    ),
                ],
            }
        )
        payment_move.action_post()
        payment_line = payment_move.line_ids.filtered(
            lambda aml: aml.account_id == payable
        )
        line = self.env["payment.return.line"].create(
            {
                "return_id": self.payment_return.id,
                "partner_id": self.partner.id,
                "reference": payment_move.ref,
            }
        )
        self.assertFalse(line._get_matching_move_lines())
        base_domain = type(line)._get_matching_move_lines_domain

        def outgoing_domain(return_line):
            return base_domain(
                return_line, amount_field="debit", account_type="liability_payable"
            )

        with patch.object(
            type(line), "_get_matching_move_lines_domain", outgoing_domain
        ):
            self.assertEqual(line._get_matching_move_lines(), payment_line)
            line.reference = payment_move.payment_reference
            self.assertEqual(line._get_matching_move_lines(), payment_line)
        self.assertFalse(line.move_line_ids)

    def test_matching_respects_overridden_line_selection(self):
        line = self.payment_return.line_ids
        line.write(
            {
                "move_line_ids": [Command.clear()],
                "reference": False,
                "amount": 0.0,
                "partner_id": False,
            }
        )
        self.assertFalse(self.payment_return._get_lines_to_match())
        with (
            patch.object(
                type(self.payment_return), "_get_lines_to_match", return_value=line
            ),
            patch.object(
                type(line),
                "_get_matching_move_lines",
                return_value=self.payment_line,
            ),
        ):
            self.payment_return.button_match()
        self.assertEqual(line.move_line_ids, self.payment_line)
        self.assertEqual(line.partner_id, self.partner)
        self.assertEqual(line.partner_name, self.partner.name)
        self.assertEqual(line.amount, self.payment_line.credit)

    def test_matching_validates_all_partners_before_writing(self):
        first_line = self.payment_return.line_ids
        first_line.write({"move_line_ids": [Command.clear()]})
        second_line = self.env["payment.return.line"].create(
            {"return_id": self.payment_return.id}
        )
        another_partner = self.env["res.partner"].create({"name": "Another customer"})
        another_invoice = self.invoice.copy({"partner_id": another_partner.id})
        another_invoice.action_post()
        another_receivable = another_invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        with (
            patch.object(
                type(first_line),
                "_get_matching_move_lines",
                side_effect=[
                    self.payment_line,
                    self.payment_line | another_receivable,
                ],
            ),
            self.assertRaises(UserError),
        ):
            (first_line | second_line)._find_match()
        self.assertFalse(first_line.move_line_ids)
        self.assertFalse(second_line.move_line_ids)

    def test_find_match_payment_reference(self):
        self.payment_move.payment_reference = "test payment reference 001"
        self.payment_return.line_ids.update(
            {
                "partner_id": False,
                "move_line_ids": [Command.clear()],
                "amount": 0.0,
                "reference": self.payment_move.payment_reference,
            }
        )
        self.payment_return.button_match()
        self.assertEqual(
            self.payment_return.line_ids[0].partner_id.id,
            self.payment_line.partner_id.id,
        )

    def test_find_match_ref_checks_duplicates_before_writing(self):
        self.payment_move.ref = "TESTMOVEXX01"
        self.payment_return.write(
            {
                "line_ids": [
                    Command.create(
                        {
                            "partner_id": False,
                            "move_line_ids": [(6, 0, [])],
                            "amount": 0.0,
                            "reference": self.payment_move.ref,
                        },
                    )
                ]
            }
        )
        with self.assertRaises(ValidationError):
            self.payment_return.button_match()
        self.assertFalse(
            self.payment_return.line_ids.filtered("reference").move_line_ids
        )

    def test_matching_checks_duplicates_across_returns_before_writing(self):
        self.payment_return.line_ids.write(
            {
                "move_line_ids": [Command.clear()],
                "reference": self.payment_move.ref,
            }
        )
        other_return = self.env["payment.return"].create(
            {
                "journal_id": self.bank_journal.id,
                "line_ids": [Command.create({"reference": self.payment_move.ref})],
            }
        )
        returns = self.payment_return | other_return
        with self.assertRaisesRegex(
            ValidationError, "Payment reference must be unique"
        ):
            returns.button_match()
        self.assertFalse(returns.line_ids.move_line_ids)

    def test_duplicate_lines(self):
        line_vals = {
            "partner_id": self.partner.id,
            "move_line_ids": [(6, 0, self.payment_line.ids)],
            "amount": self.payment_line.credit,
        }
        with self.assertRaises(ValidationError):
            self.payment_return.line_ids = [(0, 0, line_vals)]
        self.payment_return.action_confirm()
        with self.assertRaises(ValidationError):
            self.payment_return = self.env["payment.return"].create(
                {"journal_id": self.bank_journal.id, "line_ids": [(0, 0, line_vals)]}
            )

    def test_payments_widget(self):
        widget_vals = self.invoice.invoice_payments_widget
        self.assertEqual(len(widget_vals["content"]), 1)
        self.payment_return.action_confirm()
        info = self.invoice.invoice_payments_widget
        self.assertEqual(len(info["content"]), 2)
        self.assertEqual(info["content"][1]["amount"], -500.0)

    def test_reason_search_display_name(self):
        line = self.payment_return.line_ids[0]
        line.reason_id = self.reason.id
        self.assertEqual(line.reason_id.name, "Reason Test")

    def test_compute_total(self):
        self.assertEqual(self.payment_return.total_amount, 500)
        self.payment_return.write(
            {
                "line_ids": [
                    Command.create(
                        {
                            "partner_id": self.partner.id,
                            "amount": 10.5,
                            "expense_account": self.account.id,
                            "expense_partner_id": self.partner.id,
                        },
                    )
                ]
            }
        )
        self.assertEqual(self.payment_return.total_amount, 510.5)
