{
    "name": "Amazon Pay",
    "version": "18.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "summary": "Amazon Pay payment provider for Odoo",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["payment"],
    "external_dependencies": {"python": ["cryptography", "requests"]},
    "data": [
        "views/payment_amazon_pay_templates.xml",
        "data/payment_provider_data.xml",
        "views/payment_provider_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "payment_amazon_pay/static/src/js/payment_form.esm.js",
            "payment_amazon_pay/static/src/js/express_checkout_form.esm.js",
        ],
    },
    "installable": True,
    "application": False,
}
