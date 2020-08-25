{
    'name': 'Slimpay Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Slimpay Implementation',
    'version': '12.0.1.0.0',
    'description': """Slimpay Payment Acquirer""",
    'author': "Commown SCIC SAS",
    'license': "AGPL-3",
    'website': "https://commown.coop",
    'depends': ['payment', 'partner_firstname', 'base_phone'],
    'external_dependencies': {
        'python': ['hal_codec', 'iso8601', 'requests', 'phonenumbers']
    },
    'data': [
        'views/payment_views.xml',
        'views/payment_slimpay_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
