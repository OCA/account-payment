# Copyright 2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountPaymentTermAfterInvoiceMonth(TransactionCase):
    def setUp(self):
        super().setUp()
        self.payment_term_model = self.env["account.payment.term"]

    def test_after_invoice_month_days_compute(self):
        pt = self.payment_term_model.create(
            {
                "name": "5 days after end of the invoice month",
                "active": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 5,
                            "option": "after_invoice_month",
                        },
                    )
                ],
            }
        )
        res = pt.compute(10, date_ref="2021-01-15")
        self.assertEquals(
            res[0][0],
            "2021-02-05",
            "Error in the compute of 'after_invoice_month' with days",
        )

    def test_after_invoice_month_weeks_compute(self):
        pt = self.payment_term_model.create(
            {
                "name": "2 weeks day after end of the invoice month",
                "active": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "weeks": 2,
                            "option": "after_invoice_month",
                        },
                    )
                ],
            }
        )
        res = pt.compute(10, date_ref="2021-01-15")
        self.assertEquals(
            res[0][0],
            "2021-02-14",
            "Error in the compute of 'after_invoice_month' with weeks",
        )

    def test_after_invoice_month_months_compute(self):
        pt = self.payment_term_model.create(
            {
                "name": "2 months day after end of the invoice month",
                "active": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "months": 2,
                            "option": "after_invoice_month",
                        },
                    )
                ],
            }
        )
        res = pt.compute(10, date_ref="2021-01-15")
        self.assertEquals(
            res[0][0],
            "2021-03-31",
            "Error in the compute of 'after_invoice_month' with months",
        )
