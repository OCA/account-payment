# Copyright 2021 Creu Blanca - Alba Riera

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_bank_statement_line absl
        SET invoice_id = am.id
        FROM account_move am
        WHERE absl.{ifield} is not null and absl.{ifield} = am.old_invoice_id
        """.format(
            ifield=openupgrade.get_legacy_name("invoice_id")
        ),
    )
