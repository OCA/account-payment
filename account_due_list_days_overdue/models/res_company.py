# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    overdue_term_1 = fields.Integer(string='Overdue Term 1',
                                    help="First overdue term, in days")
    overdue_term_2 = fields.Integer(string='Overdue Term 2',
                                    help="Second overdue term, in days")

    overdue_term_3 = fields.Integer(string='Overdue Term 3')
    overdue_term_4 = fields.Integer(string='Overdue Term 4')

    @api.multi
    @api.constrains('overdue_term_1', 'overdue_term_2', 'overdue_term_3',
                    'overdue_term_4', 'overdue_term_5')
    def _check_overdue_terms(self):
        for rec in self:
            t1 = rec.overdue_term_1
            t2 = rec.overdue_term_2
            t3 = rec.overdue_term_3
            t4 = rec.overdue_term_4

            if (
                (t2 and t2 < t1) or
                (t3 and t3 < t2) or
                (t4 and t4 < t3)
            ):
                raise UserError(_("Aging periods are not correct"))
