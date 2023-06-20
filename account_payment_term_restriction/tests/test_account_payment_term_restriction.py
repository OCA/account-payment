# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import odoo.tests.common as common
from odoo import exceptions


@common.at_install(False)
@common.post_install(True)
class TestAccountPaymentTermRestriction(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.account_payment_term_model = cls.env["account.payment.term"]
        cls.acocunt_move_model = cls.env["account.move"]
        cls.res_partner_model = cls.env["res.partner"]

        # Create three different Payment Terms
        cls.sale_payment_term = cls._create_payment_term("Sale Payment Term", "sale")
        cls.purchase_payment_term = cls._create_payment_term(
            "Purchase Payment Term", "purchase"
        )
        cls.all_payment_term = cls._create_payment_term("All Payment Term", "all")

        # Instances
        cls.partner_id = cls.env.user.partner_id
        cls.currency_id = cls.env.ref("base.EUR")

    @classmethod
    def _create_payment_term(cls, name, applicable_on=False):
        return cls.account_payment_term_model.create(
            {"name": name, "applicable_on": applicable_on}
        )

    @classmethod
    def _create_account_move(cls, name, move_type):
        return cls.acocunt_move_model.create(
            {"name": name, "type": move_type, "currency_id": cls.currency_id.id}
        )

    def test_01_assign_payment_term_to_account_move(self):
        """
        Test to check the different scenarios when assigning payment terms to Journal Entries
        """
        # Invoice
        invoice = self._create_account_move("Test Invoice", "out_invoice")
        invoice.write({"invoice_payment_term_id": self.sale_payment_term.id})
        invoice.write({"invoice_payment_term_id": self.all_payment_term.id})
        with self.assertRaises(exceptions.ValidationError):
            invoice.write({"invoice_payment_term_id": self.purchase_payment_term.id})

        # Credit Note
        credit_note = self._create_account_move("Test Credit Note", "out_refund")
        credit_note.write({"invoice_payment_term_id": self.sale_payment_term.id})
        credit_note.write({"invoice_payment_term_id": self.all_payment_term.id})
        with self.assertRaises(exceptions.ValidationError):
            credit_note.write(
                {"invoice_payment_term_id": self.purchase_payment_term.id}
            )

        # Bill
        bill = self._create_account_move("Test Bill", "in_invoice")
        bill.write({"invoice_payment_term_id": self.purchase_payment_term.id})
        bill.write({"invoice_payment_term_id": self.all_payment_term.id})
        with self.assertRaises(exceptions.ValidationError):
            bill.write({"invoice_payment_term_id": self.sale_payment_term.id})

        # Refund
        refund = self._create_account_move("Test Refund", "in_refund")
        refund.write({"invoice_payment_term_id": self.purchase_payment_term.id})
        refund.write({"invoice_payment_term_id": self.all_payment_term.id})
        with self.assertRaises(exceptions.ValidationError):
            refund.write({"invoice_payment_term_id": self.sale_payment_term.id})

        # Miscellaneous
        entry = self._create_account_move("Test Entry", "entry")
        entry.write({"invoice_payment_term_id": self.all_payment_term.id})
        entry.write({"invoice_payment_term_id": self.sale_payment_term.id})
        entry.write({"invoice_payment_term_id": self.purchase_payment_term.id})

    def test_02_skip_check_if_context(self):
        """
        For Journal Entry, check that you can skip the check if the context is passed
        """
        invoice = self._create_account_move("Test Invoice", "out_invoice").with_context(
            skip_payment_term_restriction=True
        )
        # Check that it works for each case where it'd fail without the context
        invoice.write({"invoice_payment_term_id": self.purchase_payment_term.id})
