from odoo import api, models


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    @api.model
    def get_allowed_acquirers(self, acquirers, invoice_id=None, order_id=None):

        result = super(PaymentAcquirer, self).get_allowed_acquirers(
            acquirers, invoice_id=invoice_id, order_id=order_id
        )

        product_acquirer_restriction_mode = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("product_acquirer_settings.product_acquirer_restriction_mode")
        )

        # blank option -- fall back to res_partner_acquirers
        if not product_acquirer_restriction_mode or not order_id:
            return result

        order = self.env["sale.order"].browse(order_id)
        if not order.order_line:
            return result

        # 'first' option (and order_id)
        if product_acquirer_restriction_mode == "first":
            product_acquirer = order.order_line[
                0
            ].product_id.allowed_product_acquirer_ids
            return list(product_acquirer) or result

        # 'all' option (and order_id)
        if product_acquirer_restriction_mode == "all":
            allowed_acquirers = set()
            for line in order.order_line:
                if line.product_id.allowed_product_acquirer_ids:
                    if allowed_acquirers:
                        allowed_acquirers = allowed_acquirers.intersection(
                            set(line.product_id.allowed_product_acquirer_ids)
                        )
                    else:
                        allowed_acquirers = set(
                            line.product_id.allowed_product_acquirer_ids
                        )
            return list(allowed_acquirers) or result
