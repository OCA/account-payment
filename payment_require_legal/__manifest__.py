# Copyright 2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payment Require Legal",
    "summary": "Require legal terms acceptance before submitting a payment",
    "version": "18.0.1.0.0",
    "category": "Accounting/Payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["payment"],
    "data": [
        "views/payment_form_templates.xml",
        "views/payment_transaction_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_require_legal/static/src/js/payment_form.esm.js",
        ],
    },
}
