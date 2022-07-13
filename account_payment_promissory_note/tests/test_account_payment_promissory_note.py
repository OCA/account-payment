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
        self.payment_1 = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "payment_method_line_id": self.payment_method.id,
                "amount": 50.00,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "sale")], limit=1)
                .id,
            }
        )
        self.payment_2 = self.env["account.payment"].create(
            {
                "invoice_ids": [(4, self.invoice_1.id), (4, self.invoice_2.id)],
                "payment_type": "inbound",
                "payment_method_line_id": self.payment_method.id,
                "amount": 50.00,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "sale")], limit=1)
                .id,
            }
        )

    def test_1_onchange_promissory_note_without_invoices(self):
        self.payment_1.date_due = "2020-09-21"
        self.payment_1._onchange_promissory_note()
        self.assertFalse(self.payment_1.date_due)
        self.payment_1.promissory_note = True
        self.payment_1.date_due = "2020-09-21"
        self.payment_1._onchange_promissory_note()
        self.assertEqual(
            self.payment_1.date_due,
            datetime.datetime.strptime("2020-09-21", "%Y-%m-%d").date(),
        )

    def test_2_onchange_promissory_note_with_invoices(self):
        self.payment_2.date_due = "2020-09-21"
        self.payment_2._onchange_promissory_note()
        self.assertFalse(self.payment_2.date_due)
        self.payment_2.promissory_note = True
        self.payment_2._onchange_promissory_note()
        self.assertEqual(
            self.payment_2.date_due,
            datetime.datetime.strptime("2020-09-23", "%Y-%m-%d").date(),
        )

    def test_3_due_date_propagation(self):
        wiz_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=[self.invoice_1.id, self.invoice_2.id],
            )
        )
        wiz_form.payment_method_line_id = self.payment_method
        wiz_form.promissory_note = True
        wiz_form.group_payment = True
        wiz_form.date_due = datetime.datetime.strptime("2020-09-23", "%Y-%m-%d").date()
        wiz = wiz_form.save()
        action_vals = wiz.create_payments()
        payment = self.env["account.payment"].search(action_vals["domain"])
        for line in payment.move_line_ids:
            self.assertEqual(line.date_maturity, payment.date_due)
