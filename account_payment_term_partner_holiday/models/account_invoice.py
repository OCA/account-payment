# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from dateutil.relativedelta import relativedelta


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        _self = self
        if self.partner_id:
            _self = self.with_context(move_partner_id=self.partner_id.id)
        super(AccountInvoice, _self)._onchange_payment_term_date_invoice()

    @api.onchange("date_due")
    def _onchange_date_due_account_payment_term_partner_holiday(self):
        if self.date_due and self.payment_term_id and self.partner_id:
            new_date_due = self.date_due
            is_date_in_holiday = self.partner_id.is_date_in_holiday(new_date_due)
            if is_date_in_holiday:
                res_date_end = is_date_in_holiday[1]
                new_date_due = res_date_end + relativedelta(days=1)
            if new_date_due != self.date_due:
                self.date_due = new_date_due

    def action_move_create(self):
        """Inject a context for getting the partner when computing payment term.
        The trade-off is that we should split the call to super record per record,
        but it shouldn't impact in performance.
        """
        for item in self:
            _item = item.with_context(move_partner_id=item.partner_id.id)
            return super(AccountInvoice, _item).action_move_create()
