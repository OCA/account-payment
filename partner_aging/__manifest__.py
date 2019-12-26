# Copyright 2012 - 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Interactive Partner Aging at any date",
    "summary": "Aging as a view - invoices and credits",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/res_partner_aging_customer.xml",
        "wizard/res_partner_aging_supplier.xml",
    ],
    "installable": True,
    "application": True,
    "development_status": "Stable",
    "maintainers": ["smangukiya"],
}
