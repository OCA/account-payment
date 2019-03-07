# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models
from .camt_parser import CamtParser

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _inherit = 'payment.return.import'

    @api.model
    def _parse_file(self, data_file):
        """
        Try to parse the file as a camt.054.001.02 or fall back on next parser.
        """
        parser = CamtParser()
        try:
            _logger.debug("Try parsing as a CAMT Bank to Customer "
                          "Debit Credit Notification.")
            return parser.parse(data_file)
        except ValueError:
            _logger.debug("Payment return file was not a Direct Debit Unpaid "
                          "Report file.",
                          exc_info=True)
            return super(PaymentReturnImport, self)._parse_file(data_file)
