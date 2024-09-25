# Copyright 2019-2021 ForgeFlow S.L.
# Copyright 2024 OERP Canada <https://www.oerp.ca>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Payment Widget Amount",
    "summary": "Extends the payment widget to be able to choose the payment " "amount",
    "version": "17.0.1.0.0",
    "category": "Account-payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account"],
    "maintainers": ["ChrisOForgeFlow"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "account_payment_widget_amount/static/src/xml/account_payment.xml",
            "account_payment_widget_amount/static/src/js/account_payment_field.esm.js",
        ],
    },
}
