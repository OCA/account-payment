import logging
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info("Init returned_payment_count on invoices")
    env = api.Environment(cr, SUPERUSER_ID, {})

    invoices = env["account.invoice"].search([("returned_payment", "=", True)])
    for invoice in invoices:
        returned_reconciles = env["account.partial.reconcile"].search(
            [("origin_returned_move_ids.invoice_id", "=", invoice.id)]
        )
        invoice.write({"returned_payment_count": len(returned_reconciles)})
