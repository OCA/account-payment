# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Payment Register with Multiple Deduction",
    "version": "14.0.1.0.1",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-payment",
    "category": "Accounting",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_payment_register_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["kittiu"],
}
