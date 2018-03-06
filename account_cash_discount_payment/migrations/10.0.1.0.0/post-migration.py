# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
logger = logging.getLogger(__name__)


def update_original_amount_currency(cr):
    logger.info(
        "account.payment.line Copying amount_currency to "
        "original_amount_currency")
    sql = """
    UPDATE account_payment_line
    SET original_amount_currency = amount_currency + discount_amount
    """
    cr.execute(sql)


def migrate(cr, version):
    if not version:
        return
    update_original_amount_currency(cr)
