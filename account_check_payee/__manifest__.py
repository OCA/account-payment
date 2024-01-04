# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Check Payee",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Add payee on payment for check printing",
    "depends": ["account_check_printing"],
    "data": [
        "views/account_payment_views.xml",
        "wizard/account_payment_register_views.xml",
    ],
    "post_init_hook": "assign_payees",
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
