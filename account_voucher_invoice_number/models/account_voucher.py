# -*- coding: utf-8 -*-
# © 2015 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountVoucher(models.Model):

    @api.one
    @api.depends(
        'line_ids.move_line_id',
        'line_cr_ids.move_line_id',
        'line_dr_ids.move_line_id'
        )
    def _compute_invoices(self):
        invoices = self.env['account.invoice']
        for line in self.line_ids:
            if line.move_line_id and line.move_line_id.invoice and line.amount:
                invoices |= line.move_line_id.invoice
        self.invoice_ids = invoices
        invoices_str = ''
        for invoice in self.invoice_ids:
            if invoices_str:
                invoices_str += '; '
            invoices_str += invoice.number
        self.invoices = invoices_str

    _inherit = 'account.voucher'

    invoices = fields.Char(
        string='Invoices', store=True, readonly=True,
        compute=_compute_invoices)
    invoice_ids = fields.Many2many(
        'account.invoice', string="Invoices", store=True, readonly=True,
        compute=_compute_invoices)
