# Copyright 2023-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from lxml import etree

from odoo.tests import new_test_user, users

from odoo.addons.base.tests.common import BaseCommon


class TestAccountPaymentTermSecurity(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        account_group = "account.group_account_invoice"
        new_test_user(
            cls.env,
            login="test-account-user",
            groups=account_group,
        )
        payment_term_group = "account_payment_term_security.account_payment_term_mgmt"
        new_test_user(
            cls.env,
            login="test-acount-payment_term_mgmt-user",
            groups=f"{account_group},{payment_term_group}",
        )

    @users("test-account-user")
    def test_res_partner_01(self):
        view = self.env["res.partner"].get_view()
        doc = etree.XML(view["arch"])
        field_payment_term_id = doc.xpath("//field[@name='property_payment_term_id']")[
            0
        ]
        self.assertTrue(field_payment_term_id.attrib["readonly"])
        self.assertTrue(field_payment_term_id.attrib["force_save"])
        field_payment_term_id = doc.xpath(
            "//field[@name='property_supplier_payment_term_id']"
        )[0]
        self.assertTrue(field_payment_term_id.attrib["readonly"])
        self.assertTrue(field_payment_term_id.attrib["force_save"])

    @users("test-acount-payment_term_mgmt-user")
    def test_res_partner_02(self):
        view = self.env["res.partner"].get_view()
        doc = etree.XML(view["arch"])
        field_payment_term_id = doc.xpath("//field[@name='property_payment_term_id']")[
            0
        ]
        self.assertNotIn("readonly", field_payment_term_id.attrib)
        self.assertNotIn("force_save", field_payment_term_id.attrib)
        field_payment_term_id = doc.xpath(
            "//field[@name='property_supplier_payment_term_id']"
        )[0]
        self.assertNotIn("readonly", field_payment_term_id.attrib)
        self.assertNotIn("force_save", field_payment_term_id.attrib)

    @users("test-account-user")
    def test_account_move_01(self):
        view = self.env["account.move"].get_view()
        doc = etree.XML(view["arch"])
        field_payment_term_id = doc.xpath("//field[@name='invoice_payment_term_id']")[0]
        self.assertTrue(field_payment_term_id.attrib["readonly"])
        self.assertTrue(field_payment_term_id.attrib["force_save"])

    @users("test-acount-payment_term_mgmt-user")
    def test_account_move_02(self):
        view = self.env["account.move"].get_view()
        doc = etree.XML(view["arch"])
        field_payment_term_id = doc.xpath("//field[@name='invoice_payment_term_id']")[0]
        self.assertNotEqual(field_payment_term_id.attrib["readonly"], "1")
        self.assertNotIn("force_save", field_payment_term_id.attrib)
