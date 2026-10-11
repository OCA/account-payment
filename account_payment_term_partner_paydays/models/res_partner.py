# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class Partner(models.Model):
    _inherit = ["res.partner"]

    customer_payment_days = fields.Char(
        string="Customer Payment day(s)",
        help="The day or days when the partner does the payments. To be used "
        "for computing the invoices due date. Separate each payment day"
        " with dashes (-), commas (,) or spaces ( ).",
    )

    supplier_payment_days = fields.Char(
        string="Vendor Payment day(s)",
        help="The day or days when you do the payments to this partner. To be used "
        "for computing the bill due date. Separate each payment day with dashes"
        " (-), commas (,) or spaces ( ).",
    )

    def _get_payment_days(self):
        """Return the payment days based on the invoice type"""
        invoice_type = self.env.context.get("invoice_type")
        if invoice_type == "in_invoice":
            return self.supplier_payment_days
        if invoice_type == "out_invoice":
            return self.customer_payment_days
        return False
