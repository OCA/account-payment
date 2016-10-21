# -*- coding: utf-8 -*-
# © 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade
from openerp import pooler, SUPERUSER_ID


def migrate_payment_types(pool, cr, uid):
    # Add manually payment needed column
    cr.execute('ALTER TABLE sale_order ADD COLUMN payment_mode_id int')
    # Write in sales orders the first corresponding payment mode
    openupgrade.logged_query(
        cr,
        """
        UPDATE sale_order
        SET payment_mode_id=payment_mode.id
        FROM payment_mode
        WHERE payment_mode.%s=sale_order.payment_type""" %
        openupgrade.get_legacy_name('type'))


@openupgrade.migrate()
def migrate(cr, version):
    pool = pooler.get_pool(cr.dbname)
    migrate_payment_types(pool, cr, SUPERUSER_ID)
    # mark module to be removed
    cr.execute("UPDATE ir_module_module "
               "SET state='to remove' "
               "WHERE name = 'sale_payment'")
