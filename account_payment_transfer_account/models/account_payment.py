# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import fields, models, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    transfer_account_id = fields.Many2one(
        comodel_name='account.account', string='Transfer Account',
        domain="[('is_transfer_account', '=', True)]",
        help="Set a specific Inter-Banks Transfer account or let empty if"
        " you want to use default account.")

    @api.multi
    def post(self):
        # Generate Entries
        super(AccountPayment, self).post()

        for record in self:
            if record.payment_type == 'transfer'\
                    and record.transfer_account_id:
                # Back Journals settings
                journal_setting = record.journal_id.update_posted
                dest_journal_setting =\
                    record.destination_journal_id.update_posted

                # Change setting if account cancel is not allowed for journal
                # or destination journal
                if not (journal_setting and dest_journal_setting):
                    (record.journal_id + record.destination_journal_id).sudo()\
                        .write({'update_posted': True})

                # Get lines to change
                move_lines = record.move_line_ids.filtered(
                    lambda r: r.account_id ==
                    record.company_id.transfer_account_id)

                # Cancel entries and unreconcile items
                move_lines.mapped('move_id').button_cancel()
                move_lines.remove_move_reconcile()

                # Change account
                move_lines.write({'account_id': record.transfer_account_id.id})

                # Post entries Reconcile items again
                move_lines.mapped('move_id').post()
                move_lines.reconcile()

                # Set correct setting on journals
                if not (journal_setting and dest_journal_setting):
                    record.journal_id.sudo()\
                        .write({'update_posted': journal_setting})
                    record.destination_journal_id.sudo()\
                        .write({'update_posted': dest_journal_setting})
