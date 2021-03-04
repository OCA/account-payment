# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests
import xmltodict
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class PaymentTansaction(models.Model):
    _inherit = "payment.transaction"

    @api.multi
    def _ippay_s2s_do_payment(self, invoice):
        acquirer = self.acquirer_id
        acquirer_ref = self.payment_token_id.acquirer_ref
        if not (self.payment_token_id.save_token
                and acquirer.ippay_save_token):
            self.payment_token_id.unlink()
        amount = format(self.amount, ".2f").replace(".", "")
        transaction_type = invoice.type == "out_invoice" and "SALE" \
                           or "CREDIT"
        request = """
            <ippay>
                <TransactionType>%s</TransactionType>
                <TerminalID>%s</TerminalID>
                <Token>%s</Token>
                <TotalAmount>%s</TotalAmount>
            </ippay>""" % (
            transaction_type,
            acquirer.ippay_terminal_id,
            acquirer_ref,
            amount,
        )
        # TODO_ add verbosity parameter?
        _logger.info("Request to get IPPay Transaction ID: %s" % (request))
        try:
            r = requests.post(
                acquirer.api_url,
                data=request,
                headers={"Content-Type": "text/xml"}
            )
        except Exception as e:
            raise ValidationError(_(e))
        _logger.info("Transaction Received: %s" % (r.content))

        data = xmltodict.parse(r.content)
        response = data.get("ippayResponse")
        self.date = fields.Datetime.now()
        if response.get("ResponseText") == "APPROVED":
            self.acquirer_reference = response.get("TransactionID")
            self.state = "done"
            return True
        else:
            self.state = "cancel"
            self.state_message = (
                response.get("ErrMsg")
                or response.get("ResponseText"))
            invoice.message_post(
                body=_("IPPay Credit Card Payment DECLINED: %s - %s")
                % (response.get("ActionCode"), self.state_message,)
            )

    @api.multi
    def ippay_s2s_do_transaction(self, **kwargs):
        # kwargs needed, some automated payments pass payment_secure args
        # although these are not used for IPPay
        for transaction in self:
            inv_rec = self.invoice_ids
            for inv in inv_rec:
                if inv.type in ["out_invoice", "out_refund"]:
                    self._ippay_s2s_do_payment(invoice=inv)
