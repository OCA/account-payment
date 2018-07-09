from odoo import api, models, fields, _

class AccountPayment(models.Model):
    _inherit = "account.move"

    batch_id = fields.Integer('Batch ID')