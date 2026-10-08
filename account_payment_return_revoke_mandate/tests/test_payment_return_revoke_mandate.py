# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestPaymentReturnRevokeMandate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create({"name": "test partner"})
        cls.bank = cls.env["res.bank"].create({"name": "test bank"})
        bank_account = cls.env["res.partner.bank"].create(
            {
                "acc_number": "0023032234211123",
                "partner_id": cls.partner.id,
                "bank_id": cls.bank.id,
                "company_id": cls.company.id,
            }
        )
        cls.mandate = cls.env["account.banking.mandate"].create(
            {
                "partner_bank_id": bank_account.id,
                "signature_date": "2015-01-01",
                "company_id": cls.company.id,
            }
        )
        cls.mandate.validate()

        cls.mode_inbound = cls.env["account.payment.mode"].create(
            {
                "name": "Inbound Credit test Bank",
                "company_id": cls.company.id,
                "bank_account_link": "variable",
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
            }
        )
        cls.bank_journal = cls.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )
        cls.mode_inbound.variable_journal_ids = cls.bank_journal
        cls.mode_inbound.payment_method_id.mandate_required = True
        cls.mode_inbound.payment_order_ok = True
        cls.partner.customer_payment_mode_id = cls.mode_inbound

        cls.invoice_account = cls.env["account.account"].search(
            [
                ("account_type", "=", "asset_receivable"),
                ("company_ids", "in", [cls.company.id]),
            ],
            limit=1,
        )
        invoice_line_account = (
            cls.env["account.account"]
            .search(
                [
                    ("account_type", "=", "expense"),
                    ("company_ids", "in", [cls.company.id]),
                ],
                limit=1,
            )
            .id
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "service",
            }
        )
        invoice_vals = [
            (
                Command.create(
                    {
                        "product_id": cls.product.id,
                        "quantity": 1.0,
                        "account_id": invoice_line_account,
                        "price_unit": 200.00,
                    },
                )
            )
        ]
        cls.invoice = cls.env["account.move"].create(
            {
                "partner_id": cls.partner.id,
                "move_type": "out_invoice",
                "company_id": cls.company.id,
                "journal_id": cls.env["account.journal"]
                .search(
                    [("type", "=", "sale"), ("company_id", "=", cls.company.id)],
                    limit=1,
                )
                .id,
                "invoice_line_ids": invoice_vals,
            }
        )
        cls.invoice.action_post()
        cls.reason = cls.env["payment.return.reason"].create(
            {"code": "RTEST", "name": "Reason Test"}
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

    def test_payment_return_no_revoke_mandate(self):
        self.assertEqual(self.mandate.state, "valid")
        self.assertFalse(self.reason.revoke_mandates)
        # Create payment return
        payment_return = self.env["payment.return"].create(
            {
                "journal_id": self.bank_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "partner_id": self.partner.id,
                            "move_line_ids": [Command.set(self.payment_line.ids)],
                            "amount": self.payment_line.credit,
                            "expense_partner_id": self.partner.id,
                            "reason_id": self.reason.id,
                        },
                    )
                ],
            }
        )
        payment_return.action_confirm()
        self.assertEqual(payment_return.state, "done")
        self.assertEqual(self.mandate.state, "valid")

    @mute_logger(
        "odoo.addons.account_payment_return_revoke_mandate.models.account_move"
    )
    def test_payment_return_revoke_mandate(self):
        self.reason.revoke_mandates = True
        self.assertEqual(self.mandate.state, "valid")
        # Create payment return
        payment_return = self.env["payment.return"].create(
            {
                "journal_id": self.bank_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "partner_id": self.partner.id,
                            "move_line_ids": [Command.set(self.payment_line.ids)],
                            "amount": self.payment_line.credit,
                            "expense_partner_id": self.partner.id,
                            "reason_id": self.reason.id,
                        },
                    )
                ],
            }
        )
        payment_return.action_confirm()
        self.assertEqual(payment_return.state, "done")
        self.assertEqual(self.mandate.state, "cancel")
