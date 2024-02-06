# -*- coding: utf-8 -*-
# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = ["account.payment", "mail.thread"]
    _name = "account.payment"

    state = fields.Selection(track_visibility='always')
