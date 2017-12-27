# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# (http://www.eficent.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def do_print_checks(self):
        for rec in self:
            if rec.company_id.check_layout_id:
                return self.env['ir.actions.report']._get_report_from_name(
                    rec.company_id.check_layout_id.report
                ).report_action(self)
        return super(AccountPayment, self).do_print_checks()
