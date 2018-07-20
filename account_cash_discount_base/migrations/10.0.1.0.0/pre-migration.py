# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def migrate(cr, version):
    modules = [
        ('account_cash_discount_payment_term', 'account_cash_discount_base'),
    ]
    openupgrade.update_module_names(cr, modules, merge_modules=True)
    # recompute fields
    cr.execute(
        """
        ALTER TABLE account_invoice
            DROP COLUMN IF EXISTS discount_amount;
        ALTER TABLE account_invoice
            DROP COLUMN IF EXISTS amount_total_with_discount;
        """
    )
