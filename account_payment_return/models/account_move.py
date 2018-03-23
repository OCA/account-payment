# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    origin_returned_move_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='account_partial_reconcile_account_move_line_rel',
        column1='partial_reconcile_id',
        column2='move_line_id',
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    partial_reconcile_returned_ids = fields.Many2many(
        comodel_name='account.partial.reconcile',
        relation='account_partial_reconcile_account_move_line_rel',
        column1='move_line_id',
        column2='partial_reconcile_id',
    )
