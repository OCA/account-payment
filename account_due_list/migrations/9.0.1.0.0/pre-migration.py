# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

logger = logging.getLogger('upgrade')


def migrate(cr, version):
    logger.info("Migrating account_due_list from version %s", version)
    if not version:
        return

    cr.execute('ALTER TABLE account_move_line DROP COLUMN maturity_residual')
    cr.execute('ALTER TABLE account_move_line DROP COLUMN stored_invoice_id')
