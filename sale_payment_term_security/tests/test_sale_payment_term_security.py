# Copyright 2023-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from lxml import etree

from odoo.tests import new_test_user, users

from odoo.addons.base.tests.common import BaseCommon


class TestSalePaymentTermSecurity(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sale_group = "sales_team.group_sale_salesman"
        new_test_user(
            cls.env,
            login="test-sale-user",
            groups=sale_group,
        )
        payment_term_group = "account_payment_term_security.account_payment_term_mgmt"
        new_test_user(
            cls.env,
            login="test-sale-payment_term_mgmt-user",
            groups=f"{sale_group},{payment_term_group}",
        )

    @users("test-sale-user")
    def test_sale_order_01(self):
        view = self.env["sale.order"].get_view()
        doc = etree.XML(view["arch"])
        field_payment_term_id = doc.xpath("//field[@name='payment_term_id']")[0]
        self.assertTrue(field_payment_term_id.attrib["readonly"])
        self.assertTrue(field_payment_term_id.attrib["force_save"])

    @users("test-sale-payment_term_mgmt-user")
    def test_sale_order_02(self):
        view = self.env["sale.order"].get_view()
        doc = etree.XML(view["arch"])
        field_payment_term_id = doc.xpath("//field[@name='payment_term_id']")[0]
        self.assertNotIn("readonly", field_payment_term_id.attrib)
        self.assertNotIn("force_save", field_payment_term_id.attrib)
