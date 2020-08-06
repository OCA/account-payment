# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.multi
    def write(self, vals):
        self.ensure_one()
        # state_done_now
        state_done_now = False
        if 'state' in vals:
            if vals['state'] == 'done' and self.state != 'done':
                if self.sale_order_id:
                    state_done_now = True
        # write
        return_object = super(PaymentTransaction, self).write(vals)
        # operations
        if state_done_now:
            # done_so_customer_template_id
            if self.acquirer_id.done_so_customer_template_id:
                for sale_order_id in self.sale_order_ids:
                    # send_mail
                    if sale_order_id.user_id:
                        mcm = self.env['mail.compose.message'].sudo(
                            sale_order_id.user_id.id
                        ).create({})
                    else:
                        mcm = self.env['mail.compose.message'].sudo().create({})
                    # onchange_template_id
                    res = mcm.onchange_template_id(
                        self.acquirer_id.done_so_customer_template_id.id,
                        'comment',
                        'payment.transaction',
                        self.id
                    )
                    mail_body = res['value']['body']
                    # update
                    mcm.composition_mode = 'comment'
                    mcm.model = 'sale.order'
                    mcm.res_id = sale_order_id.id
                    mcm.record_name = sale_order_id.name
                    mcm.template_id = \
                        self.acquirer_id.done_so_customer_template_id.id
                    mcm.body = mail_body
                    mcm.subject = res['value']['subject']
                    # send_mail_action
                    mcm.send_mail_action()
            # done_so_user_id_template_id
            if self.acquirer_id.done_so_user_id_template_id:
                if self.sale_order_id:
                    mcm = self.env['mail.compose.message'].sudo().create({})
                    # onchange_template_id
                    res = mcm.onchange_template_id(
                        self.acquirer_id.done_so_user_id_template_id.id,
                        'comment',
                        'payment.transaction',
                        self.id
                    )
                    mail_body = res['value']['body']
                    # create
                    vals = {
                        'subtype_id': 2,
                        'message_type': 'notification',
                        'body': mail_body,
                        'model': 'sale.order',
                        'res_id': self.sale_order_id.id,
                        'record_name': self.sale_order_id.name
                    }
                    # add_auto_starred
                    if self.sale_order_id.user_id:
                        vals['starred_partner_ids'] = \
                            [[6, False, [self.sale_order_id.user_id.partner_id.id]]]
                    # create
                    if self.sale_order_id.user_id:
                        self.env['mail.message'].sudo(
                            self.sale_order_id.user_id.id
                        ).create(vals)
                    else:
                        self.env['mail.message'].sudo().create(vals)
            # done_payment_method_id
            if self.acquirer_id.done_account_journal_id_account_payment:
                # vals
                vals = {
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': self.partner_id.id,
                    'journal_id': self.acquirer_id.done_account_journal_id.id,
                    'amount': self.amount,
                    'currency_id': self.currency_id.id,
                    'payment_date': self.date_validate,
                    'communication': self.reference,
                    'payment_method_id': self.acquirer_id.done_payment_method_id.id,
                    'payment_transaction_id': self.id
                }
                # create
                account_payment_obj = self.env['account.payment'].sudo().create(vals)
                # post
                account_payment_obj.post()
        # return
        return return_object
