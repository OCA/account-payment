# Copyright 2020 Commown SCIC SAS (https://commown.coop)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slimpay Payment base",
    "summary": "Provides server to server implementation of Slimpay payment",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "Commown SCIC SAS, Odoo Community Association (OCA)",
    "maintainers": ["fcayre"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ["hal_codec", "iso8601"]
    },
    "depends": [
        "payment",
        "partner_firstname",
        "base_phone",
    ],
    "data": [
        "views/payment_views.xml",
        "views/payment_slimpay_templates.xml",
        "data/payment_acquirer_data.xml",
    ],
}
