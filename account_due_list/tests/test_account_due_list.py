from odoo import fields
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountDueList(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice = cls.init_invoice(
            "out_invoice",
            partner=cls.partner_a,
            invoice_date=fields.Date.from_string("2026-01-10"),
            amounts=[1000.0],
            post=True,
        )
        cls.invoice.invoice_origin = "SO-DUE-LIST"
        cls.partner_a.ref = "PARTNER-A-REF"
        cls.action = cls.env.ref("account_due_list.action_invoice_payments")

    def _due_lines(self, domain=None):
        action_domain = safe_eval(self.action.domain)
        return self.env["account.move.line"].search(action_domain + (domain or []))

    def test_receivable_line_in_due_list(self):
        receivable = self.invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        self.assertTrue(receivable)
        lines = self._due_lines([("move_id", "=", self.invoice.id)])
        self.assertEqual(lines, receivable)
        self.assertEqual(lines.date_maturity, self.invoice.invoice_date_due)

    def test_related_fields(self):
        line = self._due_lines([("move_id", "=", self.invoice.id)])
        self.assertEqual(line.invoice_origin, "SO-DUE-LIST")
        self.assertEqual(line.invoice_date, self.invoice.invoice_date)
        self.assertEqual(line.partner_ref, "PARTNER-A-REF")
        self.assertEqual(line.payment_term_id, self.invoice.invoice_payment_term_id)

    def test_invoice_user_id_stored(self):
        line = self._due_lines([("move_id", "=", self.invoice.id)])
        self.assertEqual(line.invoice_user_id, self.invoice.invoice_user_id)
        other_user = self.env["res.users"].create(
            {"name": "Due list salesperson", "login": "due_list_salesperson"}
        )
        self.invoice.invoice_user_id = other_user
        self.assertEqual(
            self.env["account.move.line"].search(
                [("invoice_user_id", "=", other_user.id)]
            ),
            self.invoice.line_ids,
        )

    def test_paid_invoice_leaves_due_list(self):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create({})._create_payments()
        lines = self._due_lines(
            [("move_id", "=", self.invoice.id), ("full_reconcile_id", "=", False)]
        )
        self.assertFalse(lines)
