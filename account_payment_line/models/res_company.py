from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    payment_line_restrict_counterpart_partner = fields.Boolean(
        string="Restrict counterpart lines to payment partner",
        help="When enabled, counterpart lines of a payment can only use the "
        "partner set on the payment header (its commercial entity). This "
        "prevents applying invoices of a partner different from the one "
        "registered in the payment.",
    )
