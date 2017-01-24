# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class ReportCheckPrint(models.AbstractModel):
    _name = 'report.account_check_printing_report_dlt103.report_check_dlt103'
    _inherit = 'report.account_check_printing_report_base.report_check_base'

    @api.multi
    def render_html(self, data):
        return super(ReportCheckPrint, self).render_html(data)
