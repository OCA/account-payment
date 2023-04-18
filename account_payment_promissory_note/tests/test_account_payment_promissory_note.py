# Copyright 2020 Tecnativa - Carlos Roca.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import datetime

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAccountPaymentPromissoryNote(TransactionCase):
    def setUp(self):
        super().setUp()
        self.payment_method = self.env.ref("account.account_payment_method_manual_in")
        self.company = self.env.ref("base.main_company")
        partner = self.env.ref("base.partner_demo")
        self.invoice_1 = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner.id,
                "invoice_date": "2020-09-14",
                "invoice_date_due": "2020-09-23",
                "move_type": "out_invoice",
                "invoice_line_ids": [(0, 0, {"name": "Test", "price_unit": 20})],
            }
        )
        self.invoice_1.action_post()
        self.invoice_2 = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner.id,
                "invoice_date": "2020-09-14",
                "invoice_date_due": "2020-09-22",
                "move_type": "out_invoice",
                "invoice_line_ids": [(0, 0, {"name": "Test", "price_unit": 20})],
            }
        )
        self.invoice_2.action_post()

    def test_1_onchange_promissory_note_without_invoices(self):
        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "payment_method_line_id": self.payment_method.id,
                "amount": 50.00,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "sale")], limit=1)
                .id,
            }
        )
        payment.date_due = "2020-09-21"
        payment._onchange_promissory_note()
        self.assertFalse(payment.date_due)
        payment.promissory_note = True
        payment.date_due = "2020-09-21"
        payment._onchange_promissory_note()
        self.assertEqual(
            payment.date_due,
            datetime.datetime.strptime("2020-09-21", "%Y-%m-%d").date(),
        )

    def test_2_onchange_promissory_note_with_invoices(self):
        wiz_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=[self.invoice_1.id, self.invoice_2.id],
            )
        )
        wiz_form.group_payment = True
        wiz = wiz_form.save()
        payment = wiz._create_payments()
        payment.date_due = "2020-09-21"
        payment._onchange_promissory_note()
        self.assertFalse(payment.date_due)
        payment.promissory_note = True
        payment._onchange_promissory_note()
        self.assertEqual(
            payment.date_due,
            datetime.datetime.strptime("2020-09-23", "%Y-%m-%d").date(),
        )

    def test_3_due_date_propagation(self):
        wiz_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=[self.invoice_1.id, self.invoice_2.id],
            )
        )
        wiz_form.promissory_note = True
        wiz_form.group_payment = True
        wiz_form.date_due = datetime.datetime.strptime("2020-09-23", "%Y-%m-%d").date()
        wiz = wiz_form.save()
        payment = wiz._create_payments()
        for line in payment.line_ids:
            self.assertEqual(line.date_maturity, payment.date_due)
