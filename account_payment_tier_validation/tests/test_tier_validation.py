# Copyright <2023> ArcheTI <info@archeti.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestPaymentTierValidation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Get payment model
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
                "email": "test@example.com",
            }
        )

        # Create tier definitions:
        cls.tier_def_obj = cls.env["tier.definition"]
        cls.tier_def_obj.create(
            {
                "model_id": cls.payment_model.id,
                "review_type": "individual",
                "reviewer_id": cls.test_user_1.id,
                "definition_domain": "[('amount', '>', 50.0)]",
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Partner for test"})

    def test_tier_validation_model_name(self):
        self.assertIn(
            "account.payment", self.tier_def_obj._get_tier_validation_model_names()
        )

    def test_under_validation_exceptions(self):
        self.assertIn(
            "name", self.env["account.payment"]._get_under_validation_exceptions()
        )

    def test_validation_payment(self):
        payment = self.env["account.payment"].create(
            {
                "partner_id": self.customer.id,
                "amount": 100.00,
            }
        )
        with self.assertRaises(ValidationError):
            payment.action_post()
        payment.amount = 40
        payment.request_validation()
        payment.with_user(self.test_user_1).validate_tier()
        payment.action_post()
        self.assertEqual(payment.state, "posted")
