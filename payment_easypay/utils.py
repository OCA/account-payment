# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


def get_account_id(provider_sudo):
    """Return the Account ID for EasyPay.

    Note: This method serves as a hook for potential future extensions.

    :param recordset provider_sudo: The provider on which the key should be read, as a
                                    sudoed `payment.provider` record.
    :return: The Account ID
    :rtype: str
    """
    return provider_sudo.easypay_account_id


def get_api_key(provider_sudo):
    """Return the API Key for EasyPay.

    Note: This method serves as a hook for potential future extensions.

    :param recordset provider_sudo: The provider on which the key should be read, as a
                                    sudoed `payment.provider` record.
    :return: The API Key
    :rtype: str
    """
    return provider_sudo.easypay_api_key


def include_customer_data(tx_sudo):
    """Include customer data from the transaction to the payload of the API request.

    Note: `self.ensure_one()`

    :param payment.transaction tx_sudo: The sudoed transaction of the payment.
    :return: The subset of the API payload that includes customer data.
    :rtype: dict
    """
    tx_sudo.ensure_one()

    return {
        "name": tx_sudo.partner_name or "",
        "email": tx_sudo.partner_email or "",
        "phone": tx_sudo.partner_phone or "",
        "key": str(tx_sudo.partner_id.id),
    }


def include_shipping_address(tx_sudo):
    """Include the shipping address of the related sales order or invoice to
    the payload.

    If no related sales order or invoice exists, the address is not included.

    Note: `self.ensure_one()`

    :param payment.transaction tx_sudo: The sudoed transaction of the payment.
    :return: The subset of the API payload that includes the shipping address.
    :rtype: dict
    """
    tx_sudo.ensure_one()

    if "sale_order_ids" in tx_sudo._fields and tx_sudo.sale_order_ids:
        order = tx_sudo.sale_order_ids[:1]
        return format_shipping_address(order.partner_shipping_id)
    elif "invoice_ids" in tx_sudo._fields and tx_sudo.invoice_ids:
        invoice = tx_sudo.invoice_ids[:1]
        return format_shipping_address(invoice.partner_shipping_id)
    return {}


def format_shipping_address(shipping_partner):
    """Format the shipping address to comply with the payload structure of the
    API request.

    :param res.partner shipping_partner: The shipping partner.
    :return: The formatted shipping address.
    :rtype: dict
    """
    return {
        "name": shipping_partner.name or shipping_partner.parent_id.name,
        "address": {
            "street": shipping_partner.street or "",
            "city": shipping_partner.city or "",
            "postal_code": shipping_partner.zip or "",
            "country": shipping_partner.country_id.code or "",
        },
    }
