# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountPaymentLineCreate(models.TransientModel):

    _inherit = 'account.payment.line.create'

    date_type = fields.Selection(
        selection_add=[
            ('discount_due_date', _("Discount Due Date")),
        ],
    )
    cash_discount_date_start = fields.Date()
    cash_discount_date_end = fields.Date()

    @api.multi
    def _prepare_move_line_domain(self):
        self.ensure_one()
        domain = super(
            AccountPaymentLineCreate, self
        )._prepare_move_line_domain()

        if self.date_type == 'discount_due_date':
            date_start = self.cash_discount_date_start
            date_end = self.cash_discount_date_end
            domain += [
                ('invoice_id.discount_due_date', '>=', date_start),
                ('invoice_id.discount_due_date', '<=', date_end),
            ]
        return domain
