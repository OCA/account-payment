# © 2015-2016 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    returned_move_line_id = fields.Many2one(
        'account.move.line', string='Returned Journal Item',
        ondelete='restrict')

    payment_line_returned = fields.Boolean(
        string='Returned',
        help='True if this payment line has been returned.')
