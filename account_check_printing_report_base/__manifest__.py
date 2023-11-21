# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# (http://www.eficent.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Check Printing Report Base",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Eficent,"
              "Serpent Consulting Services Pvt. Ltd.,"
              "Ursa Information Systems,"
              "Odoo Community Association (OCA)",
    "category": "Generic Modules/Accounting",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_check_printing",
                "report_wkhtmltopdf_param"],
    "data": [
        "security/ir.model.access.csv",
        "data/report_paperformat.xml",
        "data/account_payment_check_report_data.xml",
        "views/report_check_base.xml",
        "views/res_company_view.xml",
        "views/account_payment_check_report_view.xml",
        "report/account_check_writing_report.xml",
    ],
    "installable": True,
}
