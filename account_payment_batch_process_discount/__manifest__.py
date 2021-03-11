# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Discount on batch payments",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "maintainer": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_payment_batch_process", "account_payment_term_discount"],
    "data": [
        "views/account_move.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["mgosai"],
    "auto_install": True,
}
