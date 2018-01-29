# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payments Due list',
    'version': '11.0.1.0.0',
    'category': 'Generic Modules/Payment',
    'summary': 'Check printing commons',
    'description': """
    """,
    'website': '',
    'depends': ['account'],
    'data': [
        'views/payment_view.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
    'installable': True,
    'auto_install': False,
}
