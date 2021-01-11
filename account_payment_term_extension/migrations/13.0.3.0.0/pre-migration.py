# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        """UPDATE account_payment_term_line
        SET value_amount = value_amount_untaxed
        WHERE value = 'amount_untaxed'"""
    )
    cr.execute(
        """UPDATE account_payment_term_line
        SET value = 'percent_amount_untaxed'
        WHERE value = 'amount_untaxed'"""
    )
