# Copyright 2019 ACSONE SA/NV
# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Return Import Iso20022",
    "summary": """
        This addon allows to import payment returns from ISO 20022 files
        like PAIN or CAMT.""",
    "version": "18.0.1.1.1",
    "development_status": "Mature",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA),Tecnativa,ACSONE SA/NV",
    "website": "https://github.com/OCA/account-payment",
    "depends": [
        # OCA/account-payment
        "account_payment_return_import",
        # OCA/bank-payment
        "account_payment_order",
    ],
    "data": ["data/payment.return.reason.csv"],
}
