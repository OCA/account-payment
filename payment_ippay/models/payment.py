# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests
import xmltodict
from datetime import datetime
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError


class PaymentAcquirerIppay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('ippay', 'IPpay')])
    api_url = fields.Char("Api URL", required_if_provider='ippay')
    ippay_terminal_id = fields.Char("IPpay TerminalID",
                                    required_if_provider='ippay')

    # @api.model
    # def _get_ippaypayment_urls(self, environment):
    #     """Ippaypayment URLS."""
    #     url = 'https://staging.ippay.com/ippaygateway/PaymentProcess.aspx'
    #     if environment == 'prod':
    #         url = 'https://hostedpage.ippay.com/'
    #     return {'ippaypayment_form_url': url}

    @api.multi
    def ippay_form_generate_values(self, values):
        """Request values."""
        ippay_tx_values = dict(values)
        # ippay_tx_values.update({
        #     'tx_url': self.ippaypayments_get_form_action_url(),
        # })
        ippay_tx_values.update({
            'ippay_tx_url': '/ippay',
            'api_url': self.api_url,
            'terminal_id': self.ippay_terminal_id,
            'cc_num': '5454545454545454'
        })
        print ("\n\n\n\n ippay_tx_values", ippay_tx_values)
        return ippay_tx_values

    # @api.multi
    # def ippaypayments_get_form_action_url(self):
    #     """Get the url."""
    #     return self._get_ippaypayment_url(
    #         self.environment)['ippaypayment_form_url']

    @api.model
    def ippay_s2s_form_process(self, data):
        print (">>>>. data", data)
        values = {
            'cc_number': data.get('cc_number'),
            'cc_holder_name': data.get('cc_holder_name'),
            'cc_expiry': data.get('cc_expiry'),
            'cc_cvc': data.get('cc_cvc'),
            'cc_brand': data.get('cc_brand'),
            'acquirer_id': int(data.get('acquirer_id')),
            'partner_id': int(data.get('partner_id'))
        }
        PaymentMethod = self.env['payment.token'].sudo().create(values)
        return PaymentMethod

    @api.multi
    def ippay_s2s_form_validate(self, data):
        error = dict()
        mandatory_fields = ["cc_number", "cc_cvc", "cc_holder_name", "cc_expiry", "cc_brand"]
        # Validation
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        if data['cc_expiry']:
            # FIX we split the date into their components and check if there is two components containing only digits
            # this fixes multiples crashes, if there was no space between the '/' and the components the code was crashing
            # the code was also crashing if the customer was proving non digits to the date.
            cc_expiry = [i.strip() for i in data['cc_expiry'].split('/')]
            if len(cc_expiry) != 2 or any(not i.isdigit() for i in cc_expiry):
                return False
            try:
                if datetime.now().strftime('%y%m') > datetime.strptime('/'.join(cc_expiry), '%m/%y').strftime('%y%m'):
                    return False
            except ValueError:
                return False
        return False if error else True

    # @api.multi
    # def ippay_test_credentials(self):
    #     self.ensure_one()
    #     transaction = AuthorizeAPI(self.acquirer_id)
    #     return transaction.test_authenticate()

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    @api.model
    def ippay_create(self, values):
        print (">>>>>>>>>> values", values)
        acquirer = self.env['payment.acquirer'].browse(
            values['acquirer_id'])
        print ("values['cc_expiry", values['cc_expiry'])
        expiry = (values['cc_expiry']).split('/')
        if values.get('cc_number'):
            values['cc_number'] = values['cc_number'].replace(' ', '')
            card_detail = {'cc_number': values['cc_number'],
                           'expiry_month': values.get('cc_expiry_month') or expiry[0].replace(' ', ''),
                           'expiry_year': values.get('cc_expiry_year') or expiry[1].replace(' ', '')}

            print (">>>> card_detail", card_detail)
            xml = '''<ippay>
            <TransactionType>TOKENIZE</TransactionType>
            <TerminalID>%s</TerminalID>
            <CardNum>%s</CardNum>
            <CardExpMonth>%s</CardExpMonth>
            <CardExpYear>%s</CardExpYear>
            </ippay>''' % (acquirer.ippay_terminal_id,
                           card_detail.get('cc_number'),
                           card_detail.get('expiry_month'),
                           card_detail.get('expiry_year'))
            if acquirer.api_url:
                url = acquirer.api_url
            r = requests.post(url,
                              data=xml, headers={'Content-Type': 'text/xml'})
            data = xmltodict.parse(
                r.content)
            print ("\n\n\n>>>>> data", data)
            token = data['IPPayResponse'].get('Token')
            print (">>>>>>>> token", token)
            if token:
                return {
                    'name': 'XXXXXXXXXXXX%s - %s' % (
                        values['cc_number'][-4:], values['cc_holder_name']),
                    'acquirer_ref': token,
                }
            else:
                raise ValidationError(
                    _('Customer payment token creation in IPpay failed: %s' % (
                        data['IPPayResponse'].get('ErrMsg'))
                      ))
        else:
            return values
