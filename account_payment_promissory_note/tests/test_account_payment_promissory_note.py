# Copyright 2020 Tecnativa - Carlos Roca.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import datetime

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class TestAccountPaymentPromissoryNote(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.user.company_id
        self.default_journal_cash = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "cash")], limit=1
        )
        self.inbound_payment_method_line = (
            self.default_journal_cash.inbound_payment_method_line_ids[0]
        )
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
                "payment_method_line_id": self.inbound_payment_method_line.id,
                "amount": 50.00,
                "journal_id": self.default_journal_cash.id,
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
        for line in payment.move_id.line_ids:
            self.assertEqual(line.date_maturity, payment.date_due)
