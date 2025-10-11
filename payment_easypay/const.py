# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# EasyPay API version
API_VERSION = "2.0"

# EasyPay API endpoints
API_URL_TEST = "https://api.test.easypay.pt"
API_URL_PROD = "https://api.prod.easypay.pt"

# The codes of the payment methods to activate when EasyPay is activated.
DEFAULT_PAYMENT_METHOD_CODES = {
    # Primary payment methods.
    "card",
    # Brand payment methods.
    "visa",
    "mastercard",
}

# Supported payment methods mapping
PAYMENT_METHODS_MAPPING = {
    "cc": "Credit/Debit Card",
    # The following payment methods are supported by EasyPay API but not fully
    # implemented/tested in this module. Uncomment and test before using in production.
    # "mb": "Multibanco",
    # "mbw": "MB WAY",
    # "dd": "SEPA Direct Debit",
    # "vi": "Virtual IBAN",
    # "ap": "Apple Pay",
    # "gp": "Google Pay",
    # "sw": "Samsung Pay",
}

# Payment types
PAYMENT_TYPE_SALE = "sale"
PAYMENT_TYPE_AUTHORISATION = "authorisation"

# Mapping of transaction states to EasyPay payment statuses.
# See EasyPay API documentation for exhaustive status list.
STATUS_MAPPING = {
    "draft": (),
    "pending": ("pending",),
    "authorized": ("authorized", "authorised"),
    "done": ("success", "captured", "paid"),
    "cancel": ("cancelled",),
    "error": ("failed",),
}

# Events which are handled by the webhook
HANDLED_WEBHOOK_EVENTS = [
    "generic",
    "authorisation",
    "transaction",
]

# Supported countries (Portugal and territories where EasyPay operates)
SUPPORTED_COUNTRIES = {
    "PT",  # Portugal
}
