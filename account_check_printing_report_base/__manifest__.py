# Copyright 2016 ForgeFlow, S.L.
# (http://www.forgeflow.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2017 Tecnativa.
# Copyright 2018 iterativo.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Check Printing Report Base",
    "version": "18.0.1.0.1",
    "license": "AGPL-3",
    "author": "ForgeFlow,"
    "Serpent Consulting Services Pvt. Ltd.,"
    "Ursa Information Systems,"
    "Odoo Community Association (OCA)",
    "category": "Generic Modules/Accounting",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_check_printing"],
    "external_dependencies": {"python": ["num2words"]},
    "data": [
        "security/ir.model.access.csv",
        "data/report_paperformat.xml",
        "views/account_journal_view.xml",
        "views/report_check_base.xml",
        "report/account_check_writing_report.xml",
    ],
    "installable": True,
}
