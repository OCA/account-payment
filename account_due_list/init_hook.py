# -*- coding: utf-8 -*-
# © 2016 David Dufresne <david.dufresne@savoirfairelinux.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp import SUPERUSER_ID
from openerp.api import Environment


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
    store_field_day(cr)
    store_field_maturity_residual(cr)


def post_init_hook(cr, pool):
    env = Environment(cr, SUPERUSER_ID, {})
    store_field_maturity_residual_post_init(env)


def store_field_stored_invoice_id(cr):
    cr.execute(
        """
        ALTER TABLE account_move_line ADD COLUMN stored_invoice_id integer;
        COMMENT ON COLUMN account_move_line.stored_invoice_id IS 'Invoice';
        """)

    logger.info('Computing field stored_invoice_id on account.move.line')

    cr.execute(
        """
        UPDATE account_move_line
        SET stored_invoice_id = subquery.invoice_id
        FROM (
            SELECT line.id as move_line_id, inv.id as invoice_id
            FROM account_move_line line
            LEFT OUTER JOIN account_move move ON line.move_id = move.id
            LEFT OUTER JOIN account_invoice inv ON move.id = inv.move_id
        ) AS subquery
        WHERE account_move_line.id=subquery.move_line_id;
        """
    )


def store_field_day(cr):
    cr.execute(
        """
        ALTER TABLE account_move_line ADD COLUMN day character varying(16);
        COMMENT ON COLUMN account_move_line.day IS 'Day';
        """)

    logger.info('Computing field day on account.move.line')

    cr.execute(
        """
        UPDATE account_move_line
        SET day = subquery.date_maturity
        FROM (
            SELECT id, date_maturity FROM account_move_line
        ) AS subquery
        WHERE account_move_line.id=subquery.id;
        """
    )


def store_field_maturity_residual(cr):
    cr.execute(
        """
        ALTER TABLE account_move_line ADD COLUMN maturity_residual
        double precision;
        COMMENT ON COLUMN account_move_line.maturity_residual
        IS 'Residual Amount';
        """)

    logger.info(
        'Storing 0 as value to field amount_residual on account.move.line')

    cr.execute(
        """
        UPDATE account_move_line SET maturity_residual = 0
        """)


def store_field_maturity_residual_post_init(env):
    logger.info('Computing field amount_residual on account.move.line')

    for move_line in env['account.move.line'].search([]):
        sign = (move_line.debit - move_line.credit) < 0 and -1 or 1
        maturity_residual = move_line.amount_residual * sign
        env.cr.execute(
            """
            UPDATE account_move_line SET maturity_residual = %s WHERE id = %s
            """, (maturity_residual, move_line.id))
