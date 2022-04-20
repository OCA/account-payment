# Copyright 2019-2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Payment Widget Amount",
    "summary": "Extends the payment widget to be able to choose the payment " "amount",
    "version": "15.0.1.0.0",
    "category": "Account-payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account"],
    "data": [],
    "maintainers": ["ChrisOForgeFlow"],
    "assets": {
        "web.assets_qweb": [
            "account_payment_widget_amount/static/src/xml/account_payment.xml",
        ],
        "web.assets_backend": [
            "account_payment_widget_amount/static/src/js/account_payment_field.js",
        ],
    },
}
