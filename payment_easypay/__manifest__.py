# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Payment Provider: EasyPay",
    "version": "18.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "summary": "Payment Provider for EasyPay credit card processor",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "license": "LGPL-3",
    "depends": ["payment"],
    "data": [
        "views/payment_easypay_templates.xml",
        "views/payment_provider_views.xml",
        "data/payment_provider_data.xml",
        "data/payment_method_data.xml",
    ],
    "demo": [
        "demo/payment_provider_demo.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_easypay/static/src/js/payment_form.esm.js",
            "payment_easypay/static/src/scss/payment_easypay.scss",
        ],
    },
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
