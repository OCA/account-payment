# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Payment Return Import Sepa Camt',
    'summary': """
        This module allows the import of payment returns from
        camt.054.001.02 files.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-payment/tree/12.0/'
               'account_payment_return_import_camt',
    'depends': [
        'account_payment_return_import',
        'account_payment_order',
    ],
    'data': [
    ],
    'demo': [
    ],
}
