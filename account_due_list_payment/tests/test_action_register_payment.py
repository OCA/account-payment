# Copyright 2023 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAccountMoveLine(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountMoveLine, cls).setUpClass()

        cls.account_move_line_model = cls.env["account.move.line"]
        cls.account_payment_register_model = cls.env["account.payment.register"]

        cls.move_line = cls.account_move_line_model.search(
            [
                ("account_id.internal_type", "=", "receivable"),
                ("reconciled", "=", False),
            ],
            limit=1,
        )

    def test_action_register_payment(self):
        result = self.move_line.action_register_payment()
        self.assertEqual(result["res_model"], "account.payment.register")
        self.assertEqual(result["context"]["active_ids"], self.move_line.ids)
