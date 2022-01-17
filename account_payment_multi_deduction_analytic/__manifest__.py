# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Payment Register (Multi Deduction) - Analytic",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-payment",
    "category": "Accounting",
    "depends": [
        "account_payment_multi_deduction",
        "account_payment_deduction_analytic",
    ],
    "data": ["wizard/account_payment_register_views.xml"],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
