# Copyright 2023-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import new_test_user, users

from odoo.addons.base.tests.common import BaseCommon


class TestPaymentTermSecurity(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_account_term = "account_payment_term_security.account_payment_term_mgmt"
        new_test_user(
            cls.env,
            login="basic-user",
            groups="base.group_user",
        )
        new_test_user(
            cls.env,
            login="payment-term-mgmt-user",
            groups=f"base.group_user,{group_account_term}",
        )

    @users("basic-user")
    def test_sale_order_without_group(self):
        sale = self.env["sale.order"].new({})
        sale._compute_is_account_payment_term_mgmt()
        self.assertFalse(sale.is_account_payment_term_mgmt)

    @users("payment-term-mgmt-user")
    def test_sale_order_with_group(self):
        sale = self.env["sale.order"].new({})
        sale._compute_is_account_payment_term_mgmt()
        self.assertTrue(sale.is_account_payment_term_mgmt)
