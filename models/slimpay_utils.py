import logging
from base64 import b64encode

from iso8601 import parse_date
import requests

import coreapi
from hal_codec import HALCodec


_logger = logging.getLogger(__name__)


def get_token(api_url, app_id, app_secret):
    auth = b64encode(':'.join((app_id, app_secret)))
    resp = requests.post(
        '%s/oauth/token' % api_url,
        headers={'Accept': 'application/json',
                 'Authorization': 'Basic %s' % auth,
                 'Content-Type': 'application/x-www-form-urlencoded'},
        data={'grant_type': 'client_credentials', 'scope': 'api'})
    resp.raise_for_status()
    return resp.json()['access_token']


def get_client(api_url, app_id, app_secret, **kwargs):
    token = get_token(api_url, app_id, app_secret)
    _logger.debug('Got token %s', token)
    transport = coreapi.transports.HTTPTransport(
        headers={'Authorization': 'Bearer %s' % token})
    codec = HALCodec()
    return coreapi.Client(decoders=[codec], transports=[transport])


def _signed_date(mandate):
    return parse_date(mandate['dateSigned'])


def get_valid_mandate(client, root, **params):
    """Return the most recently signed active mandate which matches given
    criterias (see
    https://dev.slimpay.com/hapi/reference/mandates#search-mandates).
    """
    doc = client.action(
        root, 'https://api.slimpay.net/alps#search-mandates',
        params=params, action='GET')
    if 'mandates' in doc:
        ordered_valid = [m for m in sorted(doc['mandates'], key=_signed_date)
                         if m['state'] == 'active']
        if ordered_valid:
            return ordered_valid[-1]
