# -*- coding: utf-8 -*-
# © 2016 Joao Alfredo Gama Batista, Kitti U.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Voucher No Auto Lines",
    "summary": """
    When amount changes in Account Voucher, lines are not refreshed anymore
    """,
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "http://www.savoirfairelinux.com",
    "images": [],
    "author": """
    Joao Alfredo Gama Batista, Kitti U., Odoo Community Association (OCA)
    """,
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_voucher",
    ],
    "data": [
        "views/account_voucher_view.xml",
    ],
}
