# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        """
        Allows to trigger the onchange options if supplier invoice is
        created through Purchase Orders
        :return:
        """
        res = super(AccountInvoice, self)._onchange_partner_id()
        self._onchange_payment_term_discount_options()
        return res
