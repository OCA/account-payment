# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Return Import Iso20022",
    "summary": """
        This addon allows to import payment returns from ISO 20022 files
        like PAIN or CAMT.""",
    "version": "13.0.1.0.0",
    "development_status": "Mature",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA),Tecnativa,ACSONE SA/NV",
    "website": "https://github.com/OCA/account-payment/tree/12.0/"
    "account_payment_return_import_iso20022",
    "depends": [
        # OCA/account-payment
        "account_payment_return",
        "account_payment_return_import",
        # OCA/bank-payment
        "account_payment_order",
    ],
    "data": ["data/payment.return.reason.csv"],
}
