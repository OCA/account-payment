# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


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
        """Recompute the due date to the next available date according to
        the holiday periods set in the partner.

        It must only be re-calculated when a payment term is not set.
        This prevents the due date to be changed again and that another
        given number of days are added according to what is set on the
        payment term.
        """
        if self.date_due and self.partner_id and not self.payment_term_id:
            new_date_due = self.partner_id._get_valid_due_date(self.date_due)
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
