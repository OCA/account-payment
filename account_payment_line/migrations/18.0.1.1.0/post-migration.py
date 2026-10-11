from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Move the legacy single analytic account into an analytic distribution.

    The counterpart line used to store a single ``analytic_account_id``. It now
    stores an ``analytic_distribution``, so every existing line that had an
    analytic account is converted into a 100% distribution to that account.
    """
    if not openupgrade.column_exists(
        env.cr, "account_payment_counterpart_line", "analytic_account_id"
    ):
        return
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_payment_counterpart_line
        SET analytic_distribution = jsonb_build_object(analytic_account_id::text, 100)
        WHERE analytic_account_id IS NOT NULL
          AND analytic_distribution IS NULL
        """,
    )
    openupgrade.drop_columns(
        env.cr, [("account_payment_counterpart_line", "analytic_account_id")]
    )
