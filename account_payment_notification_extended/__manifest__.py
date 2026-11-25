{
    "name": "Account payment notification extended",
    "summary": "Automatic payment notifications based on company configuration",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "Odoo Community Association (OCA)",
    "maintainers": ["speardhead", "Ricardo-MC"],
    "license": "LGPL-3",
    "installable": True,
    "depends": ["account_payment_notification"],
    "data": [
        "data/ir_cron.xml",
        "views/res_config_settings_views.xml",
    ],
}
