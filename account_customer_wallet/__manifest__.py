# Copyright 2022 Coop IT Easy SCRLfs
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Customer Wallet",
    "summary": """
        Allow customers to pay using a wallet which is tracked by the company.""",
    "version": "12.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://coopiteasy.be",
    "author": "Coop IT Easy SCRLfs",
    "license": "AGPL-3",
    "application": False,
    "depends": [
        "account",
    ],
    "excludes": [],
    "data": [
        "views/account_journal_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [],
    "qweb": [],
}
