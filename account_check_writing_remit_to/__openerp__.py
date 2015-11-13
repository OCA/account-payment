# -*- coding: utf-8 -*-
# © 2015 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Check Writing using Remit-to address",
    "summary": "Module to show the remit-to address during "
               "the Check Printing.",
    "version": "7.0.1.0.0",
    "category": "Accounting",
    "website": "https://odoo-community.org/",
    "author": "Eficent, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        'account_check_writing',
        'account_voucher_remit_to'
    ],
    "data": [
        "account_check_writing_report.xml",
    ]
}
