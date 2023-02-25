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
        order = self.env["sale.order"].sudo().browse(order_id)
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
            lines = order.order_line.filtered(
                lambda l: l.product_id.allowed_product_acquirer_ids
            )
            lines_acquirers = [
                line.product_id.allowed_product_acquirer_ids for line in lines
            ]
            allowed_acquirers = set.intersection(*map(set, lines_acquirers))
            return list(allowed_acquirers) or result
