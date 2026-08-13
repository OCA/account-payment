# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

REGISTER_VIEW = "account.view_account_payment_register_form"


@tagged("post_install", "-at_install")
class TestAccountPaymentAnalyticDistribution(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.plan = cls.env["account.analytic.plan"].create(
            {"name": "Payment analytic distribution"}
        )
        cls.analytic_account_a = cls.env["account.analytic.account"].create(
            {"name": "Analytic account A", "plan_id": cls.plan.id}
        )
        cls.analytic_account_b = cls.env["account.analytic.account"].create(
            {"name": "Analytic account B", "plan_id": cls.plan.id}
        )

    def _create_bill(self, lines):
        """Post a vendor bill made of ``(price_unit, analytic_distribution)``."""
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-01-01",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Line %s" % index,
                            "quantity": 1,
                            "price_unit": price_unit,
                            "tax_ids": [Command.clear()],
                            "analytic_distribution": distribution,
                        }
                    )
                    for index, (price_unit, distribution) in enumerate(lines)
                ],
            }
        )
        bill.action_post()
        return bill

    def _register_payment(self, bill, active_id=None):
        """Register the payment of ``bill`` the way the web client does."""
        wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=bill.ids,
                active_id=bill.id if active_id is None else active_id,
            ),
            view=REGISTER_VIEW,
        )
        action = wizard_form.save().action_create_payments()
        return self.env["account.payment"].browse(action["res_id"])

    def _counterpart_line(self, payment):
        return payment._seek_for_lines()[1]

    def test_distribution_of_a_single_analytic_account(self):
        bill = self._create_bill([(1000.0, {str(self.analytic_account_a.id): 100})])

        payment = self._register_payment(bill)

        self.assertEqual(
            self._counterpart_line(payment).analytic_distribution,
            {str(self.analytic_account_a.id): 100.0},
        )

    def test_distribution_is_weighted_by_the_amounts(self):
        """A bill split 90/10 must not be paid as a 50/50 one."""
        bill = self._create_bill(
            [
                (900.0, {str(self.analytic_account_a.id): 100}),
                (100.0, {str(self.analytic_account_b.id): 100}),
            ]
        )

        payment = self._register_payment(bill)

        self.assertEqual(
            self._counterpart_line(payment).analytic_distribution,
            {
                str(self.analytic_account_a.id): 90.0,
                str(self.analytic_account_b.id): 10.0,
            },
        )

    def test_amounts_without_analytic_account_stay_unallocated(self):
        bill = self._create_bill(
            [
                (900.0, {str(self.analytic_account_a.id): 100}),
                (100.0, False),
            ]
        )

        payment = self._register_payment(bill)

        self.assertEqual(
            self._counterpart_line(payment).analytic_distribution,
            {str(self.analytic_account_a.id): 90.0},
        )

    def test_bill_without_analytic_distribution(self):
        """Nothing to copy: the payment is created without analytic items."""
        bill = self._create_bill([(1000.0, False)])

        payment = self._register_payment(bill)

        self.assertTrue(payment)
        self.assertFalse(self._counterpart_line(payment).analytic_distribution)

    def test_distribution_is_not_read_from_the_active_id(self):
        """The wizard is also opened from records that are not journal entries.

        Expense reports are the usual case: the web client keeps the
        ``hr.expense.sheet`` id in ``active_id`` while ``active_ids`` holds the
        journal entry, so the analytic distribution has to be read from the
        documents being paid, never from ``active_id``.
        """
        bill = self._create_bill([(1000.0, {str(self.analytic_account_a.id): 100})])
        last_move = self.env["account.move"].search([], order="id desc", limit=1)

        payment = self._register_payment(bill, active_id=last_move.id + 1)

        self.assertEqual(
            self._counterpart_line(payment).analytic_distribution,
            {str(self.analytic_account_a.id): 100.0},
        )

    def test_analytic_items_are_created_once_on_the_payment(self):
        bill = self._create_bill(
            [
                (900.0, {str(self.analytic_account_a.id): 100}),
                (100.0, {str(self.analytic_account_b.id): 100}),
            ]
        )

        payment = self._register_payment(bill)

        analytic_lines = self._counterpart_line(payment).analytic_line_ids
        self.assertEqual(
            {line.account_id: line.amount for line in analytic_lines},
            {self.analytic_account_a: -900.0, self.analytic_account_b: -100.0},
        )
