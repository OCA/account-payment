# © 2017 Eficent Business and IT Consulting Services S.L.
#        (http://www.eficent.com)
# © 2018 Jaume Planas <jaume.planas@minorisa.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Account Partner Reconcile",
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    'author':
        'Minorisa, S.L.,'
        'Eficent,'
        'Odoo Community Association (OCA), ',
    'website': 'https://github.com/OCA/account-payment',
    'license': 'AGPL-3',
    "depends": [
        'account',
    ],
    "data": [
        'views/res_partner_view.xml',
    ],
    "installable": True
}
