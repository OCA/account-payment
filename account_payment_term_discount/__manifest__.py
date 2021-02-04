# Copyright (C) 2010-2012 Camptocamp Austria (<http://www.camptocamp.at>)
# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Terms Discount",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "depends": ["purchase", "account"],
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "data": [
        "security/ir.model.access.csv",
        "views/account_payment_term_view.xml",
        "views/account_payment_view.xml",
        "views/account_move_view.xml",
        "views/product_view.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["hardik-osi"],
}
