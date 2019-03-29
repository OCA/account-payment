# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def _compute_invoice_vendor_references(self):
        for payment in self:
            ref = payment.invoice_ids.mapped(lambda x: x.reference or x.number)
            ref.sort()
            payment.invoice_vendor_references = ', '.join(ref)

    invoice_vendor_references = fields.Char(
        string='Ref Invoices',
        compute=_compute_invoice_vendor_references)
