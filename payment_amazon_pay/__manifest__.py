{
    "name": "Amazon Pay",
    "version": "18.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "summary": "Amazon Pay payment provider for Odoo 18",
    "license": "AGPL-3",
    "author": "OpenAI",
    "depends": ["payment"],
    "external_dependencies": {"python": ["cryptography", "requests"]},
    "data": [
        "data/payment_provider_data.xml",
        "views/payment_provider_views.xml",
        "views/payment_amazon_pay_templates.xml",
    ],
    "installable": True,
    "application": False,
}
