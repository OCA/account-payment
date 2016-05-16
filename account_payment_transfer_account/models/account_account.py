# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_transfer_account = fields.Boolean(
        string='Is Inter-Banks Transfer Account')
