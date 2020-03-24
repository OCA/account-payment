# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from lxml import etree

RE_CAMT = re.compile(r"(^urn:iso:std:iso:20022:tech:xsd:camt." r"|^ISO:camt.)")
RE_CAMT_VERSION = re.compile(
    r"(^urn:iso:std:iso:20022:tech:xsd:camt.054.001.02"
    r"|^ISO:camt.054.001.02"
    r"|^urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"
    r"|^ISO:camt.053.001.02)"
)


class CamtParser:
    """Parser for CAMT Bank to Customer Debit Credit Notification."""

    @staticmethod
    def parse_amount(ns, node):
        """Parse element that contains Amount."""
        if node is None:
            return 0.0
        amount = 0.0
        amount_node = node.xpath(
            "./ns:AmtDtls/ns:InstdAmt/ns:Amt | ./ns:AmtDtls/ns:TxAmt/ns:Amt",
            namespaces={"ns": ns},
        )
        if amount_node:
            amount = float(amount_node[0].text)
        return amount

    @staticmethod
    def parse_date(ns, node):
        """Parse element that contains date."""
        date_node = node.xpath("./ns:GrpHdr/ns:CreDtTm", namespaces={"ns": ns})
        return date_node[0].text[:10]

    @staticmethod
    def add_value_from_node(ns, node, xpath_str, obj, key, join_str=None):
        """Add value to object from first or all nodes found with xpath.

        If xpath_str is a list (or iterable), it will be seen as a series
        of search path's in order of preference. The first item that results
        in a found node will be used to set a value in the dictionary."""
        if not isinstance(xpath_str, list | tuple):
            xpath_str = [xpath_str]
        for search_str in xpath_str:
            found_node = node.xpath(search_str, namespaces={"ns": ns})
            if found_node:
                if join_str is None:
                    attr_value = found_node[0].text
                else:
                    attr_value = join_str.join([x.text for x in found_node])
                obj[key] = attr_value
                break

    def parse_transaction_details(self, ns, node, transaction):
        """
        Parse transaction details.
        """
        self.add_value_from_node(
            ns, node, "./ns:Refs/ns:EndToEndId", transaction, "reference"
        )
        self.add_value_from_node(
            ns, node, "./ns:RltdDts/ns:IntrBkSttlmDt", transaction, "date"
        )
        self.add_value_from_node(
            ns, node, "./ns:RmtInf/ns:Ustrd", transaction, "concept"
        )
        self.add_value_from_node(
            ns, node, "./ns:RltdPties/ns:Dbtr/ns:Nm", transaction, "partner_name"
        )
        self.add_value_from_node(
            ns,
            node,
            "./ns:RltdPties/ns:DbtrAcct/ns:Id/ns:IBAN",
            transaction,
            "account_number",
        )
        self.add_value_from_node(
            ns, node, "./ns:RtrInf/ns:Rsn/ns:Cd", transaction, "reason_code"
        )
        self.add_value_from_node(
            ns,
            node,
            "./ns:RtrInf/ns:AddtlInf",
            transaction,
            "reason_additional_information",
        )

    def parse_transactions(self, ns, node, transactions):
        """
        Parse transactions (entry) node.
        """
        details_nodes = node.xpath("./ns:NtryDtls/ns:TxDtls", namespaces={"ns": ns})
        entry_date = node.xpath("./ns:BookgDt/ns:Dt", namespaces={"ns": ns})
        for details_node in details_nodes:
            return_info = details_node.xpath("./ns:RtrInf", namespaces={"ns": ns})
            if not return_info:
                continue
            transaction = {}
            transaction["amount"] = self.parse_amount(ns, details_node)
            self.parse_transaction_details(ns, details_node, transaction)
            transaction["raw_import_data"] = etree.tostring(details_node)
            if not transaction.get("date"):
                transaction["date"] = entry_date[0].text
            transactions.append(transaction)
        return transactions

    def parse_payment_returns(self, ns, node):
        """
        Parse entry node.
        """
        return_date = self.parse_date(ns, node)
        payment_returns = []
        notification_nodes = node.xpath(
            "./ns:Ntfctn | ./ns:Stmt", namespaces={"ns": ns}
        )
        for notification_node in notification_nodes:
            entry_nodes = notification_node.xpath("./ns:Ntry", namespaces={"ns": ns})
            for i, entry_node in enumerate(entry_nodes):
                payment_return = {}
                self.add_value_from_node(
                    ns, notification_node, "./ns:Id", payment_return, "name"
                )
                payment_return["date"] = return_date
                self.add_value_from_node(
                    ns,
                    notification_node,
                    "./ns:Acct/ns:Id/ns:IBAN",
                    payment_return,
                    "account_number",
                )
                payment_return["transactions"] = []
                transactions = []
                self.parse_transactions(ns, entry_node, transactions)
                payment_return["transactions"].extend(transactions)
                subno = 0
                for transaction in payment_return["transactions"]:
                    subno += 1
                    transaction["unique_import_id"] = (
                        "{return_name}{entry_subno}{transaction_subno}".format(
                            return_name=payment_return["name"],
                            entry_subno=i,
                            transaction_subno=subno,
                        )
                    )
                payment_returns.append(payment_return)
        return payment_returns

    def check_version(self, ns, root):
        """
        Check the validity of the camt file.
        :raise: ValueError if not valid
        """
        # Check whether it's a CAMT Bank to Customer Debit Credit Notification
        if not RE_CAMT.search(ns):
            raise ValueError("no camt: " + ns)
        # Check the camt version
        if not RE_CAMT_VERSION.search(ns):
            raise ValueError("no camt.053.001.02 nor camt.054.001.02: " + ns)
        # Check GrpHdr element
        root_0_0 = root[0][0].tag[len(ns) + 2 :]  # strip namespace
        if root_0_0 != "GrpHdr":
            raise ValueError("expected GrpHdr, got: " + root_0_0)

    def parse(self, data):
        """
        Parse camt.054.001.02 file and camt.053 .001.02 files.
        :param data:
        :return: account.payment.return records list
        :raise: ValueError if parsing failed
        """
        root = etree.fromstring(data, parser=etree.XMLParser(recover=True))
        if root is None:
            raise ValueError("The XML file is not valid.")
        ns = root.tag[1 : root.tag.index("}")]
        self.check_version(ns, root)
        parsed_payment_returns = []
        for node in root:
            payment_returns = self.parse_payment_returns(ns, node)
            for payment_return in payment_returns:
                if payment_return["transactions"]:
                    parsed_payment_returns.append(payment_return)
        return parsed_payment_returns
