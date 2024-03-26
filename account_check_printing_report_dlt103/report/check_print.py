# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ReportCheckPrint(models.AbstractModel):
    _name = "report.account_check_printing_report_dlt103.report_check_dlt103"
    _inherit = "report.account_check_printing_report_base.report_check_base"

    @api.model
    def get_report_values(self, docids, data):
        return super(ReportCheckPrint, self).get_report_values(docids, data)
