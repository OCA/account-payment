# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def line2bank(self):
        """
        Try to return for each Ledger Posting line a corresponding bank
        account according to the payment type.  This work using one of
        the bank of the partner defined on the invoice eventually
        associated to the line.
        Return the first suitable bank for the corresponding partner.
        """
        line2bank = {}

        for line in self:
            line2bank[line.id] = False
            if line.invoice_id and line.invoice_id.partner_bank_id:
                line2bank[line.id] = line.invoice_id.partner_bank_id.id
            elif line.partner_id:
                if not line.partner_id.bank_ids:
                    line2bank[line.id] = False
                else:
                    for bank in line.partner_id.bank_ids:
                        line2bank[line.id] = bank.id
                        break
                if not line2bank.get(line.id) and line.partner_id.bank_ids:
                    line2bank[line.id] = line.partner_id.bank_ids[0].id
            else:
                raise UserError(_('There is no partner defined on the entry'
                                  ' line.'))
        return line2bank

    @api.one
    def _get_journal_entry_ref(self):
        if self.move_id.state == 'draft':
            if self.invoice.id:
                self.journal_entry_ref = self.invoice.number
            else:
                self.journal_entry_ref = '*' + str(self.move_id.id)
        else:
            self.journal_entry_ref = self.move_id.name

    journal_entry_ref = fields.Char(compute=_get_journal_entry_ref,
                                    string='Journal Entry Ref')

    @api.multi
    def get_balance(self):
        """
        Return the balance of any set of move lines.

        Not to be confused with the 'balance' field on this model, which
        returns the account balance that the move line applies to.
        """
        total = 0.0
        for line in self:
            total += (line.debit or 0.0) - (line.credit or 0.0)
        return total
