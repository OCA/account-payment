# -*- coding: utf-8 -*-
# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Payment Residual Amount",
    "summary": "Extends the view of payments to show the residual amount "
               "(amount that has not yet been reconciled)",
    "version": "10.0.1.0.0",
    "category": "Account-payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "Eficent, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account"],
    "data": [
        "views/account_payment_view.xml"
    ],
}
