# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo.tests.common import TransactionCase


class TestPaymentRefInvoice(TransactionCase):
    def setUp(self):
        super(TestPaymentRefInvoice, self).setUp()
        self.account_move = self.env["account.move"]
        self.account_model = self.env["account.account"]
        self.payment_model = self.env["account.payment"]
        self.register_payments_model = self.env[
            "account.payment.register"
        ].with_context(active_model="account.move")
        self.account_invoice_line = self.env["account.move.line"]
        self.journal_model = self.env["account.journal"]
        self.current_user = self.env.user
        self.check_journal = self.journal_model.search([("code", "=", "CHK")], limit=1)
        if not self.check_journal:
            self.check_journal = self.journal_model.create(
                {"name": "received check", "type": "bank", "code": "CHK"}
            )
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )

        # Instance: Account
        self.invoice_account = self.account_model.search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )

    def test_payment_ref_invoice(self):
        # 2 invoice, 1 payment and check invoice reference
        invoice1 = self.account_move.create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                # 'account_id': self.invoice_account.id,
                "type": "in_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "name": "Test invoice line",
                            "account_id": self.invoice_account.id,
                            "quantity": 1.00,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        invoice2 = invoice1.copy()
        invoice1.action_post()
        invoice2.action_post()
        invoice_ref = ", ".join([invoice1.name, invoice2.name])
        # Make full payment
        ctx = {
            "active_model": "account.invoice",
            "active_ids": [invoice1.id, invoice2.id],
        }

        register_payments = self.register_payments_model.with_context(ctx).create(
            {
                "payment_date": time.strftime("%Y-%m-%d"),
                "journal_id": self.check_journal.id,
                "payment_method_id": self.payment_method_manual_in.id,
                "group_payment": True,
            }
        )

        register_payments.create_payments()
        payment = self.payment_model.search([], order="id desc", limit=1)
        # Test
        self.assertEqual(payment.invoice_vendor_references, invoice_ref)
        # self.assertEqual(payment.state, 'posted')
