# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentReturnReason(models.Model):

    _inherit = 'payment.return.reason'

    revoke_mandates = fields.Boolean(company_dependent=True)
