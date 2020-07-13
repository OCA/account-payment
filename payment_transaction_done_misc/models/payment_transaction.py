# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    @api.one
    def write(self, vals):        
        #state_done_now
        state_done_now = False
        if 'state' in vals:
            if vals['state']=='done' and self.state!='done':
                if self.sale_order_id.id>0:
                    state_done_now = True                    
        #write
        return_object = super(PaymentTransaction, self).write(vals)
        #operations
        if state_done_now==True:
            #done_sale_order_customer_mail_template_id
            if self.acquirer_id.done_sale_order_customer_mail_template_id.id>0:
                for sale_order_id in self.sale_order_ids:
                    #send_mail
                    if sale_order_id.user_id.id>0:
                        mail_compose_message_obj = self.env['mail.compose.message'].sudo(sale_order_id.user_id.id).create({})
                    else:                
                        mail_compose_message_obj = self.env['mail.compose.message'].sudo().create({})
                    #onchange_template_id
                    return_mail_compose_message_obj = mail_compose_message_obj.onchange_template_id(self.acquirer_id.done_sale_order_customer_mail_template_id.id, 'comment', 'payment.transaction', self.id)
                    mail_body = return_mail_compose_message_obj['value']['body']                                            
                    #update
                    mail_compose_message_obj.composition_mode = 'comment'
                    mail_compose_message_obj.model = 'sale.order'
                    mail_compose_message_obj.res_id = sale_order_id.id
                    mail_compose_message_obj.record_name = sale_order_id.name                
                    mail_compose_message_obj.template_id = self.acquirer_id.done_sale_order_customer_mail_template_id.id
                    mail_compose_message_obj.body = mail_body
                    mail_compose_message_obj.subject = return_mail_compose_message_obj['value']['subject']                  
                    #send_mail_action
                    mail_compose_message_obj.send_mail_action()
            #done_sale_order_user_id_mail_template_id
            if self.acquirer_id.done_sale_order_user_id_mail_template_id.id > 0:
                if self.sale_order_id.id > 0:
                    mail_compose_message_obj = self.env['mail.compose.message'].sudo().create({})
                    # onchange_template_id
                    return_mail_compose_message_obj = mail_compose_message_obj.onchange_template_id(
                        self.acquirer_id.done_sale_order_user_id_mail_template_id.id, 'comment',
                        'payment.transaction', self.id)
                    mail_body = return_mail_compose_message_obj['value']['body']
                    # create
                    mail_message_vals = {
                        'subtype_id': 2,
                        'message_type': 'notification',
                        'body': mail_body,
                        'model': 'sale.order',
                        'res_id': self.sale_order_id.id,
                        'record_name': self.sale_order_id.name
                    }
                    # add_auto_starred
                    if self.sale_order_id.user_id.id > 0:
                        mail_message_vals['starred_partner_ids'] = [
                            [6, False, [self.sale_order_id.user_id.partner_id.id]]]
                    # create
                    if self.sale_order_id.user_id.id > 0:
                        mail_message_obj = self.env['mail.message'].sudo(self.sale_order_id.user_id.id).create(
                            mail_message_vals)
                    else:
                        mail_message_obj = self.env['mail.message'].sudo().create(mail_message_vals)
            #done_account_journal_id_account_payment
            if self.acquirer_id.done_account_journal_id_account_payment.id>0:
                #vals
                account_payment_vals = {
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': self.partner_id.id,
                    'journal_id': self.acquirer_id.done_account_journal_id_account_payment.id,
                    'amount': self.amount,
                    'currency_id': self.currency_id.id,
                    'payment_date': self.date_validate,
                    'communication': self.reference,
                    'payment_method_id': self.acquirer_id.done_account_journal_id_account_payment_method.id,
                    'payment_transaction_id': self.id                  
                }
                #create
                account_payment_obj = self.env['account.payment'].sudo().create(account_payment_vals)
                #post
                account_payment_obj.post()                                            
        #return
        return return_object