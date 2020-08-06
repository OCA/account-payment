# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    done_so_customer_template_id = fields.Many2one(
        comodel_name='mail.template',
        domain=[('model_id.model', '=', 'payment.transaction')],
        string='Mail template from customer',
        help='Email that will be sent to the customer when the '
             'transaction is completed and linked to a sales order'
    )
    done_so_user_id_template_id = fields.Many2one(
        comodel_name='mail.template',
        domain=[('model_id.model', '=', 'payment.transaction')],
        string='Mail template from user_id',
        help='Create an internal note related to user_id '
             'from sale_order'
    )
    done_account_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Account journal',
        help='Account journal used to create payments from '
             'transactions done'
    )
    done_payment_method_id = fields.Many2one(
        comodel_name='account.payment.method',
        domain=[('payment_type', '=', 'inbound')],
        string='Payment method',
        help='Payment method used in payment'
    )
