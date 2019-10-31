import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_cash_invoice',
        'odoo11-addon-account_check_printing_report_base',
        'odoo11-addon-account_check_printing_report_dlt103',
        'odoo11-addon-account_due_list',
        'odoo11-addon-account_due_list_aging_comment',
        'odoo11-addon-account_due_list_days_overdue',
        'odoo11-addon-account_due_list_payment_mode',
        'odoo11-addon-account_early_payment_discount',
        'odoo11-addon-account_move_line_auto_reconcile_hook',
        'odoo11-addon-account_partner_reconcile',
        'odoo11-addon-account_payment_batch_process',
        'odoo11-addon-account_payment_credit_card',
        'odoo11-addon-account_payment_return',
        'odoo11-addon-account_payment_return_import',
        'odoo11-addon-account_payment_return_import_sepa_pain',
        'odoo11-addon-account_payment_show_invoice',
        'odoo11-addon-account_payment_widget_amount',
        'odoo11-addon-account_voucher_killer',
        'odoo11-addon-partner_aging',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
