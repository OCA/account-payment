# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PaymentReturnReasonActionType(models.Model):

    _name = "payment.return.reason.action.type"
    _description = "Payment Return Reason Action Types"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer("Sequence", default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.user.company_id,
        ondelete="cascade",
    )


class PaymentReturnReason(models.Model):
    _name = "payment.return.reason"
    _description = 'Payment return reason'

    code = fields.Char()
    name = fields.Char(string='Reason', translate=True)
    next_action_type_id = fields.Many2one(
        comodel_name="payment.return.reason.action.type",
        string="Next Action",
        company_dependent=True,
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        return [(r.id, "[{code}] {name}".format(code=r.code, name=r.name))
                for r in self]
