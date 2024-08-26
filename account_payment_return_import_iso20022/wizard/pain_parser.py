# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2016 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from lxml import etree


class PainParser:
    """Parser for SEPA Direct Debit Unpaid Report import files."""

    def parse_amount(self, ns, node):
        """Parse element that contains Amount and CreditDebitIndicator."""
        if node is None:
            return 0.0
        amount = 0.0
        amount_node = node.xpath("./ns:Amt/ns:InstdAmt", namespaces={"ns": ns})
        if amount_node:
            amount = float(amount_node[0].text)
        return amount

    def parse_date(self, ns, node):
        """Parse element that contains date."""
        date_node = node.xpath("./ns:GrpHdr/ns:CreDtTm", namespaces={"ns": ns})
        return date_node[0].text[:10]

    def add_value_from_node(self, ns, node, xpath_str, obj, key, join_str=None):
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
        """Parse transaction details."""
        transaction["amount"] = self.parse_amount(ns, node)
        self.add_value_from_node(ns, node, "./ns:ReqdColltnDt", transaction, "date")
        self.add_value_from_node(
            ns, node, "./ns:RmtInf/ns:Ustrd", transaction, "concept"
        )
        self.add_value_from_node(
            ns, node, "./ns:Dbtr/ns:Nm", transaction, "partner_name"
        )
        self.add_value_from_node(
            ns, node, "./ns:DbtrAcct/ns:Id/ns:IBAN", transaction, "account_number"
        )

    def parse_transaction(self, ns, node, transaction):
        """Parse transaction (entry) node."""
        self.add_value_from_node(
            ns, node, "./ns:OrgnlEndToEndId", transaction, "reference"
        )
        self.add_value_from_node(
            ns, node, "./ns:StsRsnInf/ns:Rsn/ns:Cd", transaction, "reason_code"
        )
        self.add_value_from_node(
            ns,
            node,
            "./ns:StsRsnInf/ns:AddtlInf",
            transaction,
            "reason_additional_information",
        )
        details_node = node.xpath("./ns:OrgnlTxRef", namespaces={"ns": ns})
        if details_node:
            self.parse_transaction_details(ns, details_node[0], transaction)
        transaction["raw_import_data"] = etree.tostring(node)
        return transaction

    def parse_payment_return(self, ns, node):
        """Parse a single payment return node."""
        payment_return = {}
        self.add_value_from_node(
            ns, node, "./ns:GrpHdr/ns:MsgId", payment_return, "name"
        )
        payment_return["date"] = self.parse_date(ns, node)
        transaction_nodes = node.xpath(
            "./ns:OrgnlPmtInfAndSts/ns:TxInfAndSts", namespaces={"ns": ns}
        )
        if transaction_nodes:
            self.add_value_from_node(
                ns,
                transaction_nodes[0],
                "./ns:OrgnlTxRef/ns:CdtrAcct/ns:Id/ns:IBAN",
                payment_return,
                "account_number",
            )
        payment_return["transactions"] = []
        for entry_node in transaction_nodes:
            transaction = {}
            self.parse_transaction(ns, entry_node, transaction)
            payment_return["transactions"].append(transaction)
        # Give an unique ID to each transaction
        subno = 0
        for transaction in payment_return["transactions"]:
            subno += 1
            transaction["unique_import_id"] = payment_return["name"] + str(subno).zfill(
                4
            )
        return payment_return

    def check_version(self, ns, root):
        """Validate validity of SEPA Direct Debit Unpaid Report file."""
        # Check wether it is SEPA Direct Debit Unpaid Report at all:
        re_pain = re.compile(r"(^urn:iso:std:iso:20022:tech:xsd:pain." r"|^ISO:pain.)")
        if not re_pain.search(ns):
            raise ValueError("no pain: " + ns)
        # Check wether version 002.001.03:
        re_pain_version = re.compile(
            r"(^urn:iso:std:iso:20022:tech:xsd:pain.002.001.03"
            r"|^ISO:pain.002.001.03)"
        )
        if not re_pain_version.search(ns):
            raise ValueError("no PAIN.002.001.03: " + ns)
        # Check GrpHdr element:
        root_0_0 = root[0][0].tag[len(ns) + 2 :]  # strip namespace
        if root_0_0 != "GrpHdr":
            raise ValueError("expected GrpHdr, got: " + root_0_0)

    def parse(self, data):
        """Parse a pain.002.001.03 file."""
        try:
            root = etree.fromstring(data, parser=etree.XMLParser(recover=True))
        except etree.XMLSyntaxError:
            # ABNAmro is known to mix up encodings
            root = etree.fromstring(data.decode("iso-8859-15").encode("utf-8"))
        if root is None:
            raise ValueError("Not a valid xml file, or not an xml file at all.")
        ns = root.tag[1 : root.tag.index("}")]
        self.check_version(ns, root)
        payment_returns = []
        for node in root:
            payment_return = self.parse_payment_return(ns, node)
            if payment_return["transactions"]:
                payment_returns.append(payment_return)
        return payment_returns
