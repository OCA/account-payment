# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.one
    def _compute_invoice_vendor_references(self):
        references = ''
        for invoice in self.invoice_ids:
            if references:
                references += ', '
            if invoice.reference:
                references += invoice.reference
            else:
                references += invoice.number
        self.invoice_vendor_references = references

    invoice_vendor_references = fields.Char(
        string='Invoices',
        compute=_compute_invoice_vendor_references)
