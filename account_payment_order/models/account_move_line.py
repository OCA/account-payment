# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _
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
