# -*- coding: utf-8 -*-
# Copyright 2018 Iterativo - Manuel Marquez <buzondemam@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    check_layout_verification = fields.Selection([
        ('by_company', 'By Company'),
        ('by_journal', 'By Journal'),
        ('both', 'Both'),
    ], string='Check Layout Verification', default='by_company')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        check_layout_verification = ICPSudo.get_param(
            'account_check_printing_report_base.check_layout_verification')
        res.update(
            check_layout_verification=check_layout_verification
            if check_layout_verification else 'by_company'
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            'account_check_printing_report_base.check_layout_verification',
            self.check_layout_verification
            if self.check_layout_verification else 'by_company')
