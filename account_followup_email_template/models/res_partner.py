# -*- coding: utf-8 -*-
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _

class Partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _notify_by_email(self, message, force_send=False, send_after_commit=True, user_signature=True):
        '''
        The layout that we are going to use to format the email is sent by context
        '''
        return super(Partner, self.with_context(custom_layout='account_followup_email_template.followup_layout_email_template'))._notify_by_email(message, force_send, send_after_commit, user_signature)
