# Copyright 2020 Tecnativa - Carlos Roca.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import datetime

from odoo.tests.common import TransactionCase


class TestAccountPaymentPromissoryNote(TransactionCase):
    def setUp(self):
        super(TestAccountPaymentPromissoryNote, self).setUp()
        payment_method = self.env["account.payment.method"].create(
            {"name": "Test_MTH", "code": "TST", "payment_type": "inbound"}
        )
        self.payment_1 = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "payment_method_id": payment_method.id,
                "amount": 50.00,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "sale")], limit=1)
                .id,
            }
        )
        self.company = self.env.ref("base.main_company")
        partner = self.env.ref("base.partner_demo")
        self.payment_2 = self.env["account.payment"].create(
            {
                "invoice_ids": [
                    (
                        0,
                        0,
                        {
                            "company_id": self.company.id,
                            "partner_id": partner.id,
                            "invoice_date": "2020-09-14",
                            "invoice_date_due": "2020-09-23",
                            "type": "out_invoice",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "company_id": self.company.id,
                            "partner_id": partner.id,
                            "invoice_date": "2020-09-14",
                            "invoice_date_due": "2020-09-22",
                            "type": "out_invoice",
                        },
                    ),
                ],
                "payment_type": "inbound",
                "payment_method_id": payment_method.id,
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
