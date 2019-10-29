# Copyright 2016 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ReportCheckPrint(models.AbstractModel):
    _name = 'report.account_check_printing_report_sslm102.sslm102'
    _inherit = 'report.account_check_printing_report_base.report_check_base'
    _description = "Check sslm102"

    @api.model
    def _get_report_values(self, docids, data):
        return super(ReportCheckPrint, self)._get_report_values(docids, data)
