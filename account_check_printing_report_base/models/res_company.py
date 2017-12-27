# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# (http://www.eficent.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    check_layout_id = fields.Many2one(
        comodel_name='account.payment.check.report',
        string="Check format")
