"""Create the Ippay Payment token and acquirer."""
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests
import xmltodict
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
import logging


_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    """PaymentAcquirer."""

    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[(
        "ippay_ach", "IPPay ACH eCheck")])
    api_url = fields.Char("Api URL", required_if_provider="ippay_ach")
    ippay_ach_terminal_id = fields.Char(
        "IPpay ACH TerminalID", required_if_provider="ippay_ach"
    )
    ippay_ach_save_token = fields.Selection([
        ('none', 'Never'),
        ('ask', 'Let the customer decide'),
        ('always', 'Always')],
        string='Save Cards', default='none',
        help="This option allows customers to save their credit card "
             "as a payment token and to reuse it for a later purchase. "
             "If you manage subscriptions (recurring invoicing), "
             "you need it to automatically charge the customer when you "
             "issue an invoice.")

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super()._get_feature_support()
        res['tokenize'].append('ippay_ach')
        return res

    @api.model
    def ippay_ach_s2s_form_process(self, data):
        """Create the token when user add the details from customer Portal."""
        Token = self.env["payment.token"]
        token_id = data.get("selected_token_id")
        if not token_id:
            save_token = (
                self.ippay_ach_save_token == 'always' or
                (self.ippay_ach_save_token == 'ask' and
                 bool(data.get('save_token')))
            )
            values = {
                "save_token": save_token,
                'bank_acc_number': data.get('bank_acc_number'),
                'aba': data.get('aba'),
                'ch_holder_name': data.get('ch_holder_name'),
                'acquirer_id': int(data.get('acquirer_id')),
                'partner_id': int(data.get('partner_id'))
            }
            # Only create a new Token if it doesn't already exist
            token_code = Token._ippay_ach_get_token(values)
            payment_method = Token.sudo().search(
                [
                    ("acquirer_ref", "=", token_code),
                    ("partner_id", "=", values.get("partner_id")),
                    ("acquirer_id", "=", values.get("acquirer_id")),
                ],
                limit=1,
            )
            if not payment_method:
                payment_method = Token.sudo().create(values)
        else:
            payment_method = Token.sudo().browse(int(token_id))
        return payment_method

    @api.multi
    def ippay_ach_s2s_form_validate(self, data):
        """Check the validation of token element."""
        error = dict()
        token_id = data.get('selected_token_id')
        if not token_id:
            mandatory_fields = ["bank_acc_number", "aba"]
            # Validation
            for field_name in mandatory_fields:
                if not data.get(field_name):
                    error[field_name] = 'missing'
            return False if error else True
        return True


class PaymentToken(models.Model):
    """Payment Token."""

    _inherit = "payment.token"

    # By default, keep the Token for future transactions
    # This is the case when creating from the backend
    # When collected from the Portal, the user is asked,
    # and it may be set to False to be used only for the current transaction
    save_token = fields.Boolean(default=True)

    @api.model
    def _ippay_ach_get_token(self, values):
        acquirer = self.env["payment.acquirer"].browse(values["acquirer_id"])
        check_detail = {
            "acc_number": values["bank_acc_number"],
            "aba": values["aba"]}
        xml = """
            <ippay>
                <TransactionType>TOKENIZE</TransactionType>
                <TerminalID>%s</TerminalID>
                <ABA>%s</ABA>
                <AccountNumber>%s</AccountNumber>
            </ippay>""" % (
            acquirer.ippay_ach_terminal_id,
            check_detail.get("aba"),
            check_detail.get("acc_number"),
        )
        r = requests.post(
            acquirer.api_url, data=xml, headers={"Content-Type": "text/xml"}
        )
        _logger.info("Token received: %s" % (r.content))
        data = xmltodict.parse(r.content)
        ippay_response = data.get("IPPayResponse") or data.get("ippayResponse")
        token = ippay_response.get("Token")
        if not token:
            raise ValidationError(_(
                "Customer payment token creation in"
                " IPpay ACH failed: %s - %s%s")
                % (
                    ippay_response.get("ActionCode"),
                    ippay_response.get("ErrMsg", ""),
                    ippay_response.get("ResponseText", ""),)
            )
        else:
            return token

    @api.model
    def ippay_ach_create(self, values, token_code=None):
        """Create the Ippay ACH Token."""
        # Search if the card was already stored
        # We use the last four digits for this
        existing = self.sudo().search(
            [("partner_id", "=", values.get("partner_id")),
             ("acquirer_id", "=", values.get("acquirer_id"))]
            ).filtered(lambda s: s.name[-4:] == values["cc_number"][:-4])
        if existing:
            raise ValidationError(
                _("This payment method is already assigned to this Customer.")
            )
        # In case we already know the token assigned, just use it
        token_code = token_code or self._ippay_ach_get_token(values)
        return {
            "name": "%s - %s"
            % (values["bank_acc_number"], values["ch_holder_name"]),
            "acquirer_ref": token_code,
        }
