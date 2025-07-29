# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form, TransactionCase


class TestAccountFinancialDiscountCommon(TransactionCase):
    @classmethod
    def init_invoice(
        cls,
        partner,
        move_type,
        payment_term=None,
        invoice_date=None,
        currency=None,
        payment_reference=None,
    ):
        move_form = Form(
            cls.env["account.move"].with_context(default_move_type=move_type)
        )
        move_form.partner_id = partner
        move_form.invoice_payment_term_id = payment_term
        move_form.invoice_date = invoice_date
        if currency is not None:
            move_form.currency_id = currency
        if payment_reference is not None:
            move_form.payment_reference = payment_reference
        return move_form.save()

    @classmethod
    def init_invoice_line(
        cls, invoice, quantity, unit_price, product=None, with_tax=True
    ):
        with Form(invoice) as move_form:
            with move_form.invoice_line_ids.new() as line_form:
                if product:
                    line_form.product_id = product
                line_form.name = product and product.name or "test"
                line_form.quantity = quantity
                line_form.price_unit = unit_price
                if with_tax:
                    if invoice.move_type in ("out_invoice", "in_refund"):
                        tax = cls.sale_tax
                    elif invoice.move_type in ("in_invoice", "out_refund"):
                        tax = cls.purchase_tax
                    line_form.tax_ids = tax

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.usd_currency = cls.env.ref("base.USD")
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.eur_currency.active = True
        cls.chf_currency = cls.env.ref("base.CHF")
        cls.chf_currency.active = True

        cls.partner = cls.env["res.partner"].create(
            {"name": "Peter Muster AG", "supplier_rank": 1}
        )
        cls.customer = cls.env["res.partner"].create(
            {"name": "Hans Muster GmbH & Co. KG", "customer_rank": 1}
        )

        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "Skonto",
                "early_discount": True,
                "discount_days": 10,
                "discount_percentage": 2.0,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value_amount": 100,
                            "value": "percent",
                            "nb_days": 60,
                            "delay_type": "days_after",
                        },
                    )
                ],
            }
        )

        cls.sale_tax = cls.env.company.account_sale_tax_id
        cls.purchase_tax = cls.env.company.account_purchase_tax_id

        cls.bank_journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.env.company.id), ("type", "=", "bank")],
            limit=1,
        )
        cls.eur_bank_journal = cls.env["account.journal"].create(
            {
                "name": "Bank EUR",
                "type": "bank",
                "code": "BNK2",
                "currency_id": cls.eur_currency.id,
            }
        )

        cls.payment_thirty_net = cls.env.ref("account.account_payment_term_30days")
