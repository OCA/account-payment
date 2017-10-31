# -*- coding: utf-8 -*-
# Copyright 2017 Mhadhbi Achraf(https://github.com/AMhadhbi).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models, api, _
from odoo.exceptions import UserError


class AccountPaymentConfirm(models.TransientModel):
    """
    This wizard will confirm the all the selected draft payments
    """

    _name = "account.payment.confirm"
    _description = "Confirm the selected payments"

    @api.multi
    def payment_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['account.payment'].browse(active_ids):
            if record.state != 'draft':
                raise UserError(_("Selected payment(s) cannot be confirmed as they are not in 'Draft' state."))
            record.post()
        return {'type': 'ir.actions.act_window_close'}