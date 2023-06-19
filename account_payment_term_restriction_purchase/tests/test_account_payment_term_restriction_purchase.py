# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import odoo.tests.common as common
from odoo import exceptions

from odoo.addons.account_payment_term_restriction.tests import (
    test_account_payment_term_restriction,
)


@common.at_install(False)
@common.post_install(True)
class TestAccountPaymentTermRestrictionPurchase(
    test_account_payment_term_restriction.TestAccountPaymentTermRestriction
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.purchase_order_model = cls.env["purchase.order"]

    @classmethod
    def _create_po(cls, name):
        return cls.purchase_order_model.create(
            {"name": name, "partner_id": cls.partner_id.id}
        )

    def test_01_assign_payment_term_to_purchase_order(self):
        """
        Test to check the different scenarios when assigning payment terms to Purchase Order
        """
        po = self._create_po("Test PO")
        po.write({"payment_term_id": self.purchase_payment_term.id})
        po.write({"payment_term_id": self.all_payment_term.id})
        with self.assertRaises(exceptions.ValidationError):
            po.write({"payment_term_id": self.sale_payment_term.id})

    def test_02_assign_payment_term_to_partner(self):
        """
        Test to check the different scenarios when assigning supplier payment terms to
        Partner
        """
        partner = self.partner_id
        partner.write({"property_payment_term_id": self.all_payment_term.id})
        partner.write({"property_payment_term_id": self.sale_payment_term.id})
        with self.assertRaises(exceptions.ValidationError):
            partner.write({"property_payment_term_id": self.purchase_payment_term.id})

    def test_03_skip_check_if_context(self):
        """
        For a PO and a Partner check that you can skip the check if the context is
        passed
        """
        po = self._create_po("Test PO").with_context(skip_payment_term_restriction=True)
        partner = self.partner_id.with_context(skip_payment_term_restriction=True)
        # Check that it works for each case where it'd fail without the context
        po.write({"payment_term_id": self.sale_payment_term.id})
        partner.write({"property_supplier_payment_term_id": self.sale_payment_term.id})
