# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import datetime

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("-at_install", "post_install")
class TestPromissoryNoteBranches(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.branch_a = cls._create_company(
            name="Branch A", parent_id=cls.env.company.id
        )
        cls.branch_b = cls._create_company(
            name="Branch B", parent_id=cls.env.company.id
        )

    def test_register_payment_branches(self):
        """Paying invoices of two branches, with only the branches selected,
        creates the payment in their parent company and sets the promissory
        note on it."""
        branches = self.branch_a | self.branch_b
        invoices = self.env["account.move"]
        for branch in branches:
            invoices |= self.init_invoice(
                "out_invoice",
                amounts=[100.0],
                company=branch,
                post=True,
            )
        wizard = (
            self.env["account.payment.register"]
            .with_context(
                allowed_company_ids=branches.ids,
                active_model="account.move",
                active_ids=invoices.ids,
            )
            .create(
                {
                    "group_payment": True,
                    "promissory_note": True,
                    "date_due": datetime.date(2026, 12, 31),
                }
            )
        )
        payments = wizard._create_payments()
        self.assertEqual(payments.company_id, self.env.company)
        self.assertTrue(payments.promissory_note)
        self.assertEqual(payments.date_due, datetime.date(2026, 12, 31))
