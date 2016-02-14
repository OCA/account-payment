# -*- coding: utf-8 -*-
# © <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Voucher No Auto Lines",
    "summary": "No more refresh lines when change amount in Account Voucher",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "http://www.savoirfairelinux.com",
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
