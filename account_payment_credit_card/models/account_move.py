# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        # set variables
        move_line_pool = self.env['account.move.line']

        for move in self:

            result = []
            # check whether journal has Transfer AP to Credit Card
            # Company = checked or not
            if move.journal_id and\
                    move.journal_id.credit_card:

                # browse move lines
                for move_line in move.line_ids:
                    # prepare move line values
                    result.append({
                        'name': move_line.name,
                        'ref': move_line.ref,
                        'partner_id':
                            move.journal_id.partner_id and
                            move.journal_id.partner_id.id or
                            move_line.partner_id and
                            move_line.partner_id.id or False,
                        'journal_id':
                            move_line.journal_id and move_line.journal_id.id,
                        'account_id':
                            move_line.account_id and move_line.account_id.id,
                        'debit': move_line.credit,
                        'credit': move_line.debit,
                        'date_maturity': move_line.date_maturity,
                        'move_id':
                            move_line.move_id and move_line.move_id.id,
                        'date': move_line.date
                    })

                # check result list
                if result:

                    # create new move lines
                    for vals in result:
                        move_line_pool.create(vals)

        return super(AccountMove, self).post()
