# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):

        # Call super method
        res = super(AccountMove, self).post()

        # Set variables
        move_line_pool = self.env['account.move.line']
        result = []

        # Check whether journal has Transfer AP to Credit Card Company checked
        # or not
        if self.journal_id and self.journal_id.credit_card:

            # Browse move lines
            for move_line in self.line_ids:

                # Prepare move line values
                result.append({
                    'name': move_line.name,
                    'ref': move_line.ref,
                    'partner_id': self.journal_id.partner_id and self.journal_id.partner_id.id or move_line.partner_id and move_line.partner_id.id or False,  # noqa
                    'journal_id': move_line.journal_id and move_line.journal_id.id,  # noqa
                    'account_id': move_line.account_id and move_line.account_id.id,  # noqa
                    'debit': move_line.credit,
                    'credit': move_line.debit,
                    'date_maturity': move_line.date_maturity,
                    'move_id': move_line.move_id and move_line.move_id.id,
                    'date': move_line.date
                })

        # Check result list
        if result:

            # Create new move lines
            for vals in result:
                move_line_pool.create(vals)

        return res
