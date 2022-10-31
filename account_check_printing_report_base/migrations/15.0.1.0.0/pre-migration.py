# Copyright 2022 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def set_account_check_printing_layout(env):
    # Change in companies
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_company
        SET account_check_printing_layout = CASE
            WHEN check_layout_id = %s
                THEN 'account_check_printing_report_base.action_report_check_base'
            WHEN check_layout_id = %s
                THEN 'account_check_printing_report_base.action_report_check_base_a4'
            ELSE 'disabled'
            END
        """,
        (
            env.ref(
                "account_check_printing_report_base.account_payment_check_report_base"
            ),
            env.ref(
                "account_check_printing_report_base.account_payment_check_report_base_a4"
            ),
        ),
    )
    # Change in journals
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_journal
        SET account_check_printing_layout = CASE
            WHEN check_layout_id = %s
                THEN 'account_check_printing_report_base.action_report_check_base'
            WHEN check_layout_id = %s
                THEN 'account_check_printing_report_base.action_report_check_base_a4'
            ELSE NULL
            END
        """,
        (
            env.ref(
                "account_check_printing_report_base.account_payment_check_report_base"
            ),
            env.ref(
                "account_check_printing_report_base.account_payment_check_report_base_a4"
            ),
        ),
    )


@openupgrade.migrate()
def migrate(env, version):
    set_account_check_printing_layout(env)
