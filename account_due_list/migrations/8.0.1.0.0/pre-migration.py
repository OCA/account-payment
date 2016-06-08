# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


column_drops = {
    ('account_move_line', 'day'),
}


@openupgrade.migrate()
def migrate(cr, version):
    if not version:
        return

    openupgrade.drop_columns(cr, column_drops)
