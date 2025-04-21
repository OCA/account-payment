# Copyright 2025 Spearhead - Ricardo Jara
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAccountPayment(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Payment model
        cls.payment_model = cls.env.ref("account.model_account_payment")

        # Create users
        group_ids = (
            cls.env.ref("base.group_system")
            + cls.env.ref("account.group_account_manager")
        ).ids
        cls.test_user_1 = cls.env["res.users"].create(
            {
                "name": "John",
                "login": "test1",
                "groups_id": [(6, 0, group_ids)],
                "email": "test@examlple.com",
            }
        )

        # Create tier definitions:
        cls.tier_def_obj = cls.env["tier.definition"]
        cls.tier_def_obj.create(
            {
                "model_id": cls.payment_model.id,
                "review_type": "individual",
                "reviewer_id": cls.test_user_1.id,
                "definition_domain": "[('amount', '>', 100)]",
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Partner for test"})

    def test_01_tier_definition_models(self):
        res = self.tier_def_obj._get_tier_validation_model_names()
        self.assertIn("account.payment", res)

    def test_02_validation_account_payment(self):
        payment = self.env["account.payment"].create(
            {
                "amount": 200.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.customer.id,
            }
        )

        with self.assertRaises(ValidationError):
            payment.action_post()
        payment.amount = 100
        payment.action_post()
        self.assertEqual(payment.state, "in_process")

    def test_03_validation_account_payment(self):
        payment = self.env["account.payment"].create(
            {
                "amount": 200.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.customer.id,
            }
        )
        payment.invalidate_model()
        self.assertEqual(payment.validation_status, "no")
        reviews = payment.with_user(self.env.user.id).request_validation()
        payment.invalidate_model()
        self.assertEqual(payment.validation_status, "waiting")
        self.assertTrue(reviews)
        record = payment.with_user(self.test_user_1.id)
        record.invalidate_model()
        record.validate_tier()
        payment.action_post()
        self.assertEqual(payment.state, "in_process")
        self.assertEqual(payment.validation_status, "validated")
