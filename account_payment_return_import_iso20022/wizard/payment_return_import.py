# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models
from .camt_parser import CamtParser
from .pain_parser import PainParser

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _inherit = 'payment.return.import'

    @api.model
    def _parse_file(self, data_file):
        """
        Try to parse the file as the following format or fall back on next
        parser:
            - camt.054.001.02
            - pain.002.001.03
        """
        camt_parser = CamtParser()
        pain_parser = PainParser()
        try:
            _logger.debug("Try parsing as a CAMT Bank to Customer "
                          "Debit Credit Notification.")
            return camt_parser.parse(data_file)
        except ValueError:
            try:
                _logger.debug("Try parsing as a PAIN Direct Debit Unpaid "
                              "Report.")
                return pain_parser.parse(data_file)
            except ValueError:
                _logger.debug("Payment return file is not a ISO20022 "
                              "supported file.", exc_info=True)
                return super(PaymentReturnImport, self)._parse_file(data_file)
