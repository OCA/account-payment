# Copyright 2020 Antoni Romera
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET returned_payment = ai.returned_payment
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id""",
    )
    openupgrade.load_data(
        env.cr, "account_payment_return", "migrations/13.0.1.0.0/noupdate_changes.xml"
    )
