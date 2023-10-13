# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Cash Discount Reconciliation Write off display",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "category": "Accounting",
    "depends": ["account_cash_discount_payment", "account_reconciliation_widget"],
    "data": [],
    "qweb": [
        "static/src/xml/reconcile_info_popover.xml",
    ],
    "installable": True,
}
