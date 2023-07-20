# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Command, Date
from odoo.tests.common import TransactionCase


class TestAccountCashDiscountWriteOff(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountMove = cls.env["account.move"]
        cls.MoveLine = cls.env["account.move.line"]
        cls.PaymentLineCreate = cls.env["account.payment.line.create"]
        cls.PaymentOrder = cls.env["account.payment.order"]
        cls.Journal = cls.env["account.journal"]
        cls.Account = cls.env["account.account"]

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
        cls.company = cls.env.ref("base.main_company")
        cls.purchase_journal = cls.Journal.create(
            {
                "name": "Purchase journal",
                "type": "purchase",
                "code": "PUR",
                "company_id": cls.company.id,
            }
        )
        cls.partner = cls.env.ref("base.res_partner_2")

        cls.account_expense = cls.Account.create(
            {
                "account_type": "expense",
                "company_id": cls.company.id,
                "name": "Test expense",
                "code": "TE.1",
            }
        )

        cls.early_pay_25_percents_10_days = cls.env["account.payment.term"].create(
            {
                "name": "25% discount if paid within 10 days",
                "company_id": cls.company.id,
                "line_ids": [
                    Command.create(
                        {
                            "value": "balance",
                            "days": 0,
                            "discount_percentage": 25,
                            "discount_days": 10,
                        }
                    )
                ],
            }
        )

    def _create_supplier_invoice(self, ref):
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "move_type": "in_invoice",
                "ref": ref,
                "date": Date.today(),
                "invoice_date": Date.today(),
                "invoice_payment_term_id": self.early_pay_25_percents_10_days.id,
                "payment_mode_id": self.payment_mode_out.id,
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "product_id": self.env.ref("product.product_product_4").id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "name": "product that cost 100",
                            "account_id": self.account_expense.id,
                        },
                    )
                ],
            }
        )

        return invoice

    def test_cash_discount_with_write_off(self):
        payment_mode = self.payment_mode_out
        discount_due_date = Date.today()

        invoice = self._create_supplier_invoice("test-ref")
        invoice.action_post()

        payment_order = self.PaymentOrder.create(
            {
                "payment_mode_id": payment_mode.id,
                "payment_type": "outbound",
                "journal_id": self.bank_ing_journal.id,
            }
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": discount_due_date,
                "date_type": "discount_due_date",
            }
        )

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        payment_order.draft2open()

        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)

        payment_order.open2generated()

        payment_order.generated2uploaded()

        payment_move_lines = payment_order.payment_line_ids.payment_ids.move_id.line_ids
        write_off_line = self.MoveLine.search(
            [
                ("id", "in", payment_move_lines.ids),
                ("name", "=", "Early Payment Discount"),
            ]
        )

        self.assertEqual(len(write_off_line), 1)
        self.assertEqual(write_off_line.credit, 25)

        write_off_base_line = self.MoveLine.search(
            [
                ("id", "!=", write_off_line.id),
                ("move_id", "=", write_off_line.move_id.id),
            ]
        )

        self.assertTrue(write_off_base_line)

        self.assertEqual(invoice.payment_state, "paid")
