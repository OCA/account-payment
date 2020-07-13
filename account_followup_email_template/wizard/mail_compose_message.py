# -*- coding: utf-8 -*-
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail_action(self):
        '''
        The layout that we are going to use to format the email is sent by context
        '''
        ctx = self.env.context.copy()
        if self.template_id and self.template_id.id == self.env.ref('account_followup_email_template.followup_edi_email_template').id:
            ctx.update({'custom_layout': 'account_followup_email_template.followup_layout_email_template'})
        return super(MailComposer, self.with_context(ctx)).send_mail_action()
