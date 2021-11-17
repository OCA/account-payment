# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

from .camt_parser import CamtParser
from .pain_parser import PainParser

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _inherit = "payment.return.import"

    @api.model
    def _xml_split_file(self, data_file):
        """BNP France is known to merge xml files"""
        if not data_file.startswith(b"<?xml"):
            return [data_file]
        data_file_elements = []
        all_files = data_file.split(b"<?xml")
        for file in all_files:
            if file:
                data_file_elements.append(b"<?xml" + file)
        return data_file_elements

    @api.model
    def _parse_file(self, data_file):
        data_file_elements = self._xml_split_file(data_file)
        payment_returns = []
        for data_file_element in data_file_elements:
            payment_returns.extend(self._parse_single_document(data_file_element))
        return payment_returns

    @api.model
    def _parse_single_document(self, data_file):
        """
        Try to parse the file as the following format or fall back on next
        parser:
            - camt.054.001.02
            - pain.002.001.03
        """
        camt_parser = CamtParser()
        pain_parser = PainParser()
        try:
            _logger.debug(
                "Try parsing as a CAMT Bank to Customer " "Debit Credit Notification."
            )
            return camt_parser.parse(data_file)
        except ValueError:
            try:
                _logger.debug("Try parsing as a PAIN Direct Debit Unpaid " "Report.")
                return pain_parser.parse(data_file)
            except ValueError:
                _logger.debug(
                    "Payment return file is not a ISO20022 " "supported file.",
                    exc_info=True,
                )
                return super()._parse_file(data_file)
