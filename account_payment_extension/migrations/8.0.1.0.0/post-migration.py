# -*- coding: utf-8 -*-
# © 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade


def migrate_payment_mode_partner(cr):
    payment_matrix = [
        ('customer_payment_mode', 'payment_type_customer'),
        ('supplier_payment_mode', 'payment_type_supplier'),
    ]
    for new_field_name, old_field_name in payment_matrix:
        # Write partner property for the first corresponding payment mode
        cr.execute("SELECT id FROM ir_model_fields "
                   "WHERE model='res.partner' "
                   "AND name=%s", (new_field_name, ))
        field_id = cr.fetchone()[0]
        openupgrade.logged_query(
            cr,
            """
            UPDATE ir_property
            SET fields_id=%%s,
                name=%%s,
                value_reference='payment.mode,' ||
                                 to_char(payment_mode.id, '9999999999999')
            FROM payment_mode
            WHERE payment_mode.%s=
                  to_number(
                    substring(ir_property.value_reference from 14 for 20),
                              '9999999999999')
            AND ir_property.name=%%s
            AND ir_property.value_reference LIKE 'payment.type,%s'""" %
            (openupgrade.get_legacy_name('type'), "%%"),
            (field_id, new_field_name, old_field_name))


@openupgrade.migrate()
def migrate(cr, version):
    migrate_payment_mode_partner(cr)
    # Mark new modules to be installed...
    cr.execute("UPDATE ir_module_module "
               "SET state='to install' "
               "WHERE name IN "
               "('account_banking_payment_export',"
               " 'account_payment_partner',"
               " 'account_direct_debit')")
