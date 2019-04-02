{
    'name': 'Slimpay Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Slimpay Implementation',
    'version': '10.0.1.1.5',
    'description': """Slimpay Payment Acquirer""",
    'author': "Commown SCIC SAS",
    'license': "AGPL-3",
    'website': "https://commown.fr",
    'depends': ['website_sale', 'partner_firstname', 'base_phone'],
    'external_dependencies': {
        'python': ['coreapi', 'hal_codec', 'iso8601', 'requests',
                   'phonenumbers', 'regex']
    },
    'data': [
        'views/payment_views.xml',
        'views/payment_slimpay_templates.xml',
        'views/address_template.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
