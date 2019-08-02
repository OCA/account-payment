# Copyright 2017 Open Source Integrators <http://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):
        for move in self:
            result = []
            # Check whether journal has Transfer AP to Credit Card
            # Company = checked or not
            if move.journal_id and move.journal_id.credit_card:
                # Browse move lines
                for move_line in move.line_ids:
                    # prepare move line values
                    result.append({
                        'name': move_line.name,
                        'ref': move_line.ref,
                        'partner_id':
                            move.journal_id.partner_id.id or
                            move_line.partner_id.id or False,
                        'journal_id': move_line.journal_id.id,
                        'account_id': move_line.account_id.id,
                        'debit': move_line.credit,
                        'credit': move_line.debit,
                        'date_maturity': move_line.date_maturity,
                        'move_id': move_line.move_id.id,
                        'date': move_line.date
                    })
                # Check result list
                if result:
                    # Create new move lines
                    for vals in result:
                        self.env['account.move.line'].create(vals)
        return super(AccountMove, self).post(invoice=invoice)
