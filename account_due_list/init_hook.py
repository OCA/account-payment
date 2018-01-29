# © 2016 David Dufresne <david.dufresne@savoirfairelinux.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    The objective of this hook is to speed up the installation
    of the module on an existing Odoo instance.

    Without this script, if a database has a few hundred thousand
    journal entries, which is not unlikely, the update will take
    at least a few hours.

    The pre init script only writes 0 in the field maturity_residual
    so that it is not computed by the install.

    The post init script sets the value of maturity_residual.
    """
    store_field_stored_invoice_id(cr)
    store_field_invoice_user_id(cr)


def store_field_stored_invoice_id(cr):

    cr.execute("""SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_move_line' AND
    column_name='stored_invoice_id'""")
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE account_move_line ADD COLUMN stored_invoice_id integer;
            COMMENT ON COLUMN account_move_line.stored_invoice_id IS 'Invoice';
            """)

    logger.info('Computing field stored_invoice_id on account.move.line')

    cr.execute(
        """
        UPDATE account_move_line aml
        SET stored_invoice_id = inv.id
        FROM account_move AS am, account_invoice AS inv
        WHERE am.id = aml.move_id
        AND am.id = inv.move_id
        """
    )


def store_field_invoice_user_id(cr):

    cr.execute("""SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_move_line' AND
    column_name='invoice_user_id'""")
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE account_move_line ADD COLUMN invoice_user_id integer;
            COMMENT ON COLUMN account_move_line.invoice_user_id IS
            'Invoice salesperson';
            """)

    logger.info('Computing field invoice_user_id on account.move.line')

    cr.execute(
        """
        UPDATE account_move_line aml
        SET invoice_user_id = inv.user_id
        FROM account_invoice AS inv
        WHERE aml.stored_invoice_id = inv.id
        """
    )
