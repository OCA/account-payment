# Copyright 2024 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tools.sql import column_exists


def migrate(cr, version):
    if not column_exists(cr, "account_payment_term_line", "discount"):
        return
    cr.execute(
        """UPDATE account_payment_term_line
        SET discount_percentage = discount
        WHERE discount IS NOT NULL and discount_percentage IS NULL"""
    )
