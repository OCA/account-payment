# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.depends(
        'move_id.line_id.under_payment',
        'move_id.line_id.reconcile_id.line_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids',
    )
    def _check_payment(self):
        for invoice in self:
            invoice.under_payment = any(
                [x.under_payment for x in invoice.move_id.line_id])

    under_payment = fields.Boolean(
        'Under Payment', readonly=True, store=True, compute=_check_payment)
