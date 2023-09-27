#  Copyright 2023 Simone Rubino - TAKOBI
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentRegister(AccountTestInvoicingCommon):
    def _create_payment_wizard(self, invoice, **wizard_values):
        wizard_action = invoice.action_register_payment()
        wizard_model = wizard_action["res_model"]
        wizard_context = wizard_action["context"]
        wizard_form = Form(self.env[wizard_model].with_context(**wizard_context))
        for field_name, field_value in wizard_values.items():
            setattr(wizard_form, field_name, field_value)
        wizard = wizard_form.save()
        return wizard

    def test_keep_amount(self):
        """If "Keep Previous Amount" is enabled,
        the amount is preserved when the Journal is changed."""
        # Arrange: Pay 100 for an invoice
        invoice = self.init_invoice(
            "out_invoice",
            amounts=[
                100,
            ],
            post=True,
        )
        payment_amount = 100
        payment_wizard = self._create_payment_wizard(
            invoice,
            amount=payment_amount,
            keep_previous_amount=True,
        )
        # pre-condition
        self.assertEqual(
            payment_wizard.amount,
            payment_amount,
        )
        self.assertTrue(payment_wizard.keep_previous_amount)

        # Act: Change Journal
        payment_wizard.journal_id = self.company_data["default_journal_cash"]

        # Assert: Amount is kept
        self.assertEqual(
            payment_wizard.amount,
            payment_amount,
        )

    def test_no_keep_amount(self):
        """If "Keep Previous Amount" is disabled,
        the amount is not preserved when the Journal is changed."""
        # Arrange: Pay 100 for an invoice
        invoice = self.init_invoice(
            "out_invoice",
            amounts=[
                100,
            ],
            post=True,
        )
        payment_amount = 100
        payment_wizard = self._create_payment_wizard(
            invoice,
            amount=payment_amount,
        )
        # pre-condition
        self.assertEqual(
            payment_wizard.amount,
            payment_amount,
        )
        self.assertFalse(payment_wizard.keep_previous_amount)

        # Act: Change Journal
        payment_wizard.journal_id = self.company_data["default_journal_cash"]

        # Assert: Amount is changed
        self.assertNotEqual(
            payment_wizard.amount,
            payment_amount,
        )
