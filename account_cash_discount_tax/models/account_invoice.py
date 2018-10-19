# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def action_add_cash_discount_tax_lines(self):
        wizard_obj = self.env['account.invoice.cash.tax.wizard']
        for invoice in self:
            if invoice.state != 'draft':
                raise ValidationError(
                    _('You cannot add Cash Discount Lines on Invoices that are'
                      'not draft!')
                )
            wizard = wizard_obj.create({
                'invoice_id': invoice.id,
            })
            wizard.doit()
        return True
