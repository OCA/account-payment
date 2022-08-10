# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form

from odoo.addons.account_cash_discount_base.tests.common import (
    TestAccountCashDiscountCommon,
)


class TestAccountCashDiscountPaymentCommon(TestAccountCashDiscountCommon):
    @classmethod
    def setUpClass(cls):
        super(TestAccountCashDiscountPaymentCommon, cls).setUpClass()
        cls.PaymentLineCreate = cls.env["account.payment.line.create"]
        cls.PaymentOrder = cls.env["account.payment.order"]

        cls.payment_mode_out = cls.env.ref(
            "account_payment_mode.payment_mode_outbound_ct1"
        )
        cls.bank_ing = cls.env.ref("base.bank_ing")
        cls.partner_bank_ing = cls.env.ref("base_iban.bank_iban_main_partner")

        cls.bank_ing_journal = cls.Journal.create(
            {
                "name": "ING Bank",
                "code": "ING-B",
                "type": "bank",
                "bank_id": cls.bank_ing.id,
            }
        )

    def create_supplier_invoice(
        self, date, payment_mode, amount, discount_percent, taxes
    ):

        invoice_form = Form(
            self.AccountMove.with_context(
                default_move_type="in_invoice",
                default_company_id=self.company.id,
                default_journal_id=self.purchase_journal.id,
                default_payment_mode_id=payment_mode.id,
                default_ref="reference",
            )
        )
        invoice_form.partner_id = self.partner_agrolait
        invoice_form.invoice_date = date
        invoice_form.discount_due_date = date
        invoice_form.discount_percent = discount_percent

        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.quantity = 1
            line_form.account_id = self.exp_account
            line_form.price_unit = amount
            line_form.tax_ids.clear()
            for tax in taxes:
                line_form.tax_ids.add(tax)

        invoice = invoice_form.save()
        return invoice
