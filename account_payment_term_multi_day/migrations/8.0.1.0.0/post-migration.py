# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.openupgrade import openupgrade


def update_paydays(cr):
    """
    If column paydays exists in account_payment_term then module paydays was
    installed. We must propagate paydays to account_payment_term_line to avoid
    to lose data.
    """
    if not openupgrade.column_exists(
            cr, 'account_payment_term', 'paydays'):
        return
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_payment_term_line aptl
        SET paydays = apt.paydays
        FROM account_payment_term apt
        WHERE apt.id = aptl.payment_id
    """)


@openupgrade.migrate(no_version=True)
def migrate(cr, version):
    update_paydays(cr)
