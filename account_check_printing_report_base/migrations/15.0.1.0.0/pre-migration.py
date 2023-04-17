# Copyright 2022 Tecnativa - Carlos Roca
# Copyright 2023 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def set_account_check_printing_layout(env):
    # Change in companies
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_company
        SET account_check_printing_layout = imd.module ||'.'|| imd.name
            FROM ir_model_data imd
            WHERE imd.module='account_check_printing_report_base'
                AND imd.model='account.payment.check.report'
                AND imd.res_id=res_company.check_layout_id
        """,
    )
    # Change in journals
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE account_journal ADD COLUMN
            IF NOT EXISTS account_check_printing_layout VARCHAR
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_journal
        SET account_check_printing_layout = imd.module ||'.'|| imd.name
            FROM ir_model_data imd
            WHERE imd.module='account_check_printing_report_base'
                AND imd.model='account.payment.check.report'
                AND imd.res_id=account_journal.check_layout_id
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    set_account_check_printing_layout(env)
