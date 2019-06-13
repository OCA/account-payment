# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Interactive Partner Aging at any date',
    'summary': 'Aging as a view - invoices and credits',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Open Source Integrators, Odoo Community Association (OCA)',
    'category': 'Accounting & Finance',
    'website': 'https://github.com/OCA/account-payment',
    'depends': [
        'account_invoicing',
        'account_voucher',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/res_partner_aging_customer.xml',
        'wizards/res_partner_aging_supplier.xml',
    ],
    'installable': True,
    'application': True,
}
