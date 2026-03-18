# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import requests
from werkzeug import urls
from odoo.exceptions import ValidationError
from odoo.addons.payment_taler.utils.utils import tawarn, tadebug, taerror, talog
from odoo.tools import _

def getMerchantConfiguration(url):
    url += "/config"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TalerOdoo",
    }
    tadebug("Url: ", url)
    tadebug("Headers: ", headers)
    response = requests.request("GET", url, headers=headers)
    tadebug("Response received: ", response.text)
    if response.status_code != 200:
        taerror("Error getting merchant config, bad response: ", response.text)
        raise ValidationError(_("There was an issue connecting to the Taler Merchant URL, please make sure the URL is correct and the service is up."))
    return response.json()

def requestGetToken(model):
    tadebug("Running requestGetToken")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_url = getTalerUrl(model)
    url = taler_url + "/private/token"

    payload = {"scope": "write"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TalerOdoo",
        "Authorization": "Bearer secret-token:" + getTalerPassword(model)
    }
    tadebug("Url: ", url)
    tadebug("Headers: ", headers)
    tadebug("Payload: ", payload)

    response = requests.request("POST", url, json=payload, headers=headers)
    tadebug("Response received: ", response.text)
    if response.status_code != 200:
        taerror("Error getting token, bad response: ", response.text)
        raise ValidationError(_("Error while connecting to the Taler Merchant"))
    if "token" not in response.json():
        taerror("Error getting new token: ", response.text)
        raise ValidationError(_("Error while connecting to the Taler Merchant"))

    # Set the new token value directly on the payment provider object
    model.provider_id.taler_token = response.json()["token"]
    tadebug("New token: ", model.provider_id.taler_token)

def getOrderTalerUri(model, order_id):
    tadebug("Running getOrderTalerUri")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_url = getTalerUrl(model)
    url = taler_url + "/private/orders/" + order_id

    #The following request requires an empty payload
    payload = ""
    headers = {
        "User-Agent": "TalerOdoo/insomnia/11.3.0",
        "Authorization": "Bearer " + getCurrentTalerToken(model)
    }
    tadebug("Url: ", url)
    tadebug("Headers: ", headers)
    tadebug("Payload: ", payload)

    response = requests.request("GET", url, data=payload, headers=headers)
    tadebug("Response received: ", response.text)
    if response.status_code != 200:
        taerror("Error getting order taler payment URI, bad response: ", response.text)
        return ""
    if "taler_pay_uri" not in response.json():
        taerror("Error getting taler_pay_uri field: ", response.text)
        return ""

    return response.json()["taler_pay_uri"]

def postPlaceOrderWithFulfillmentMessage(model, currency, amount, summary, fulfillment_message, pay_deadline=None):
    tadebug("Running postPlaceOrderWithFulfillmentMessage")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_url = getTalerUrl(model)
    url = taler_url + "/private/orders"

    payload = {
        "order": {
            "amount": currency + ":" + str(amount),
            "summary": summary,
            "fulfillment_message": fulfillment_message,
        },
        "create_token": False
    }
    #If a pay_deadline, in epoch seconds, is sent as parameter, include the value to the order creation object
    if pay_deadline:
        payload["order"]["pay_deadline"] = {"t_s": pay_deadline}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TalerOdoo/insomnia/11.3.0",
        "Authorization": "Bearer " + getCurrentTalerToken(model)
    }
    tadebug("Url: ", url)
    tadebug("Headers: ", headers)
    tadebug("Payload: ", payload)

    response = requests.request("POST", url, json=payload, headers=headers)
    tadebug("Response received: ", response.text)
    if response.status_code != 200:
        taerror("Error placing order, bad response: ", response.text)
        if response.json()["hint"] == "The order creation request is invalid because the given payment deadline is in the past.":
            taerror("The invoice due date is in the past, the Taler order cannot be created. Epoch time set for the invoice: " + pay_deadline)
            raise ValidationError(_("The invoice due date is in the past, the Taler order cannot be created. Please see the logs for more details."))
        raise ValidationError(_("Wrong response code. The Taler order cannot be created."))
    if "order_id" not in response.json():
        taerror("Error getting new order_id: ", response.text)
        raise ValidationError(_("Received no Order ID from Taler. The order cannot be created."))

    order_id = response.json()["order_id"]
    order_url = taler_url + "/orders/" + order_id
    order_uri = getOrderTalerUri(model, order_id)
    tadebug("Order_id: ", order_id)

    return order_id, order_url, order_uri

def postPlaceOrderWithFulfillmentUrl(model, currency, amount, summary, fulfillment_message, fulfillment_url, pay_deadline=None):
    tadebug("Running postPlaceOrderWithFulfillmentUrl")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_url = getTalerUrl(model)
    odoo_base_url = model.provider_id.get_base_url()
    url = taler_url + "/private/orders"

    payload = {
        "order": {
            "amount": currency + ":" + str(amount),
            "summary": summary,
            "fulfillment_message": fulfillment_message,
            'fulfillment_url': urls.url_join(odoo_base_url, fulfillment_url + "/" + model.reference)
        },
        "create_token": False
    }
    # If a pay_deadline, in epoch seconds, is sent as parameter, include the value to the order creation object
    if pay_deadline:
        payload["order"]["pay_deadline"] = {"t_s": pay_deadline}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TalerOdoo/insomnia/11.3.0",
        "Authorization": "Bearer " + getCurrentTalerToken(model)
    }
    tadebug("Url: ", url)
    tadebug("Headers: ", headers)
    tadebug("Payload: ", payload)

    response = requests.request("POST", url, json=payload, headers=headers)
    tadebug("Response received: ", response.text)
    if response.status_code != 200:
        taerror("Error placing order, bad response: ", response.text)
        if response.json()["hint"] == "The order creation request is invalid because the given payment deadline is in the past.":
            raise ValidationError(_("The invoice due date is in the past. The Taler order cannot be created. Epoch time set for the invoice: " + pay_deadline))
        if response.json()["code"] == 2514:
            raise ValidationError(_("You are trying to pay in a currency that is not supported by the chosen Taler merchant. Please reach out to the shop administator."))
        raise ValidationError(_("Bad response code. The Taler order cannot be created."))
    if "order_id" not in response.json():
        taerror("Error getting new order_id: ", response.text)
        raise ValidationError(_("Received no Order ID from Taler. The order cannot be created."))

    order_id = response.json()["order_id"]
    order_url = taler_url + "/orders/" + order_id
    order_uri = getOrderTalerUri(model, order_id)
    tadebug("Order_id: ", order_id)

    return order_id, order_url, order_uri

def requestRefundForOrder(model, amount, currency, reason):
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_url = getTalerUrl(model)
    url = taler_url + "/private/orders/" + model.taler_order_id + "/refund"
    payload = {
        "refund": currency + ":" + str(amount),
        "reason": reason
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TalerOdoo/insomnia/11.3.0",
        "Authorization": "Bearer " + getCurrentTalerToken(model)
    }
    tadebug("URL: ", url)
    tadebug("Headers: ", headers)
    tadebug("Payload: ", payload)

    response = requests.request("POST", url, json=payload, headers=headers)
    tadebug("Response received: ", response.text)
    if response.status_code != 200:
        taerror("Error getting order from id, bad response: ", response.text)
        raise ValidationError(_("Method called on wrong model"))

    refund_uri = response.json()["taler_refund_uri"]

    return refund_uri

def requestGetOrderFromId(model):
    tadebug("Running requestGetOrderFromId")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_url = getTalerUrl(model)
    url = taler_url + "/private/orders/" + model.taler_order_id

    # The following request requires an empty payload
    payload = ""
    headers = {
        "User-Agent": "TalerOdoo",
        "Authorization": "Bearer " + getCurrentTalerToken(model)
    }
    tadebug("Built URL: ", url)
    tadebug("Headers: ", headers)
    tadebug("Payload: ", payload)
    response = requests.request("GET", url, data=payload, headers=headers)
    tadebug("Response received: ", response.text)
    if response.status_code != 200:
        taerror("Error getting order from id, bad response: ", response.text)
        return

    return response.json()

def checkOrderIsPaid(model):
    tadebug("Running checkOrderIsPaid")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    response = requestGetOrderFromId(model)
    tadebug(response["order_status"])
    return response["order_status"] == "paid"

def getOrderIdStatus(model):
    tadebug("Running getOrderIdStatus")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    response = requestGetOrderFromId(model)
    tadebug("Order status:" + response["order_status"])
    if response == "":
        taerror("getOrderIdStatus encountered couldn't find the order on the merchant's server.")
        return
    if(not (response["contract_terms"]["order_id"] or response["order_status"])):
        taerror("getOrderIdStatus the response has invalid data. Response: ", response.text)
        return
    return response["contract_terms"]["order_id"], response["order_status"]

def getTalerUrl(model):
    # Get Taler merchant url from the payment provider object
    tadebug("Running getTalerUrl")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_url = model.provider_id.taler_merchant_url
    if not taler_url or taler_url == "":
        raise Exception(_("Taler URL is empty or incorrect. Did you set it correctly in the provider view?"))
    return taler_url

def getTalerPassword(model):
    # Get Taler merchant password from the payment provider object
    tadebug("Running getTalerPassword")
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_password = model.provider_id.taler_merchant_password
    if not taler_password or taler_password == "":
        raise Exception(_("Taler Password is empty or incorrect. Did you set it correctly in the provider view?"))
    return taler_password

def getCurrentTalerToken(model):
    tadebug("Running getCurrentTalerToken")
    # Get the current Taler merchant token from the payment provider object
    if not validateModel(model):
        raise ValidationError(_("Method called on wrong model"))
    taler_token = model.provider_id.taler_token
    if not taler_token or taler_token == "":
        raise Exception(_("Taler Token is empty"))
    return taler_token

def validateModel(model):
    if model._name != "payment.transaction" and model._name != "account.move":
        taerror("Method called on wrong model. Model used is: " + model._name + " Looking for payment.transaction or account.move.")
        return False
    else:
        return True
