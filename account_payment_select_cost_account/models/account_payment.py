from odoo import models, fields, api


class Payment(models.Model):
    _inherit = 'account.payment'
    force_destination_account_id = fields.Many2one(
        'account.account', string="Cost account")

    @api.onchange("destination_account_id")
    def onchange_destination_account_id(self):
        if self.destination_account_id:
            self.force_destination_account_id = self.destination_account_id.id

    def _get_counterpart_move_line_vals(self, invoice=False):
        vals = super(Payment, self)._get_counterpart_move_line_vals(invoice)
        if self.force_destination_account_id:
            vals['account_id'] = self.force_destination_account_id.id
        return vals

    @api.multi
    def action_draft(self):
        res = super(Payment, self).action_draft()
        for p in self:
            if not p.force_destination_account_id and p.destination_account_id:
                p.force_destination_account_id = p.destination_account_id.id
