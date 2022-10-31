# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Interactive Partner Aging for any date",
    "version": "15.0.1.0.0",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "summary": "Aging as a view - invoices and credits (OSI)",
    "category": "Accounting & Finance",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account", "account_accountant"],
    "license": "AGPL-3",
    "data": [
        "wizard/partner_aging_customer.xml",
        "wizard/partner_aging_supplier.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
