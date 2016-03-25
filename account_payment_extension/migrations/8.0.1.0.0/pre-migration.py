# -*- coding: utf-8 -*-
# © 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade
from openerp import pooler, SUPERUSER_ID

column_renames = {
    'payment_mode': [
        ('type', None),
    ],
}


def migrate_payment_types(pool, cr, uid):
    # Add manually payment needed columns
    cr.execute('ALTER TABLE account_invoice ADD COLUMN payment_mode_id int')
    cr.execute('ALTER TABLE payment_mode ADD COLUMN active bool')
    # Remove some constraints
    cr.execute('ALTER TABLE payment_mode ALTER journal DROP NOT NULL')
    cr.execute('ALTER TABLE payment_mode ALTER bank_id DROP NOT NULL')
    cr.execute('ALTER TABLE bank_type_payment_type_rel DROP CONSTRAINT '
               'bank_type_payment_type_rel_pay_type_id_fkey')
    # Rename many2many table
    cr.execute('ALTER TABLE bank_type_payment_type_rel RENAME TO '
               'bank_type_payment_type_rel_old')
    cr.execute('ALTER INDEX bank_type_payment_type_rel_pay_type_id_index '
               'RENAME TO bank_type_payment_type_rel_pay_type_id_index_old')
    cr.execute('ALTER INDEX bank_type_payment_type_rel_bank_type_id_index '
               'RENAME TO bank_type_payment_type_rel_bank_type_id_index_old')
    # Switch payment types by payment modes
    cr.execute("SELECT id, name, active, company_id FROM payment_type")
    payment_types = cr.fetchall()
    for payment_type in payment_types:
        if payment_type[3]:
            applicable_companies_ids = [payment_type[3]]
        else:
            cr.execute("SELECT id FROM res_company")
            applicable_companies_ids = [x[0] for x in cr.fetchall()]
        for company_id in applicable_companies_ids:
            # Update payment modes
            cr.execute("""SELECT id, name FROM payment_mode
                          WHERE type=%s""", (payment_type[0], ))
            payment_modes = cr.fetchall()
            for payment_mode in payment_modes:
                openupgrade.logged_query(
                    cr,
                    """
                    UPDATE payment_mode
                    SET name=%s, active=%s
                    WHERE id=%s""", (
                        "%s (%s)" % (payment_type[1], payment_mode[1]),
                        payment_type[2], payment_mode[0])
                )
            # Create at least one payment mode for each payment type
            if not payment_modes:
                # Search for a journal
                cr.execute("""SELECT id FROM account_journal
                              WHERE active=TRUE
                              AND company_id=%s
                              AND type='bank'
                              LIMIT 1""",
                           (company_id, ))
                row = cr.fetchone()
                journal_id = row and row[0] or None
                # Search for a bank account
                cr.execute("""SELECT rpb.id FROM res_partner_bank rpb
                              INNER JOIN res_partner rp ON rpb.partner_id=rp.id
                              INNER JOIN res_company rc ON rc.partner_id=rp.id
                              WHERE rc.id=%s
                              LIMIT 1""", (company_id, ))
                row = cr.fetchone()
                bank_id = row and row[0] or None
                # Create the payment mode
                openupgrade.logged_query(
                    cr,
                    """
                    INSERT INTO payment_mode
                    (name, active, journal, bank_id, company_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;""", (payment_type[1], payment_type[2],
                                       journal_id, bank_id, company_id))
                payment_modes = cr.fetchall()
            # Write in invoices the first corresponding payment mode
            openupgrade.logged_query(
                cr,
                """
                UPDATE account_invoice
                SET payment_mode_id=%s
                WHERE payment_type=%s""",
                (payment_modes[0][0], payment_type[0]))


def migrate_payment_order(cr):
    # Add manually new payment type column
    cr.execute(
        'ALTER TABLE payment_order ADD COLUMN payment_order_type varchar')
    # Map types
    openupgrade.logged_query(
        cr, """
        UPDATE payment_order
        SET payment_order_type='payment'
        WHERE type='payable'""")
    openupgrade.logged_query(
        cr, """
        UPDATE payment_order
        SET payment_order_type='debit'
        WHERE type='receivable'""")


@openupgrade.migrate()
def migrate(cr, version):
    pool = pooler.get_pool(cr.dbname)
    migrate_payment_types(pool, cr, SUPERUSER_ID)
    migrate_payment_order(cr)
    openupgrade.rename_columns(cr, column_renames)
    # Mark old module to be removed
    cr.execute("UPDATE ir_module_module "
               "SET state='to remove' "
               "WHERE name = 'account_payment_extension'")
