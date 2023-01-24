from odoo import api, models


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    @api.model
    def get_allowed_acquirers(self, acquirers, invoice_id=None, order_id=None):
        """
        Get allowed acquirers by the customer
        :param list acquirers: list of acquirers
        :param int invoice_id: invoice id
        :param int order_id: quotation id
        :return list: List of allowed acquirers
        """
        if order_id:
            model = "sale.order"
            rec_id = order_id
        elif invoice_id:
            model = "account.move"
            rec_id = invoice_id
        else:
            return acquirers
        record = self.env[model].sudo().browse(rec_id)
        customer_acquirers = record.partner_id.allowed_acquirer_ids
        return (
            list(set(acquirers) & set(customer_acquirers))
            if customer_acquirers
            else acquirers
        )
