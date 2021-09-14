# Copyright 2021 Creu Blanca

from openupgradelib import openupgrade

_column_renames = {
    "account_bank_statement_line": [("invoice_id", None)],
}


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _column_renames)
