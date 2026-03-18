# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import uuid
import logging
import qrcode
import base64
from datetime import datetime, time, timedelta
from io import BytesIO

_logger = logging.getLogger(__name__)

def talog(*args):
    log = ""
    for arg in args:
        log += str(arg)
    _logger.info(log)

def tadebug(*args):
    log = ""
    for arg in args:
        log += str(arg)
    _logger.debug(log)

def tawarn(*args):
    log = ""
    for arg in args:
        log += str(arg)
    _logger.warning(log)

def taerror(*args):
    log = ""
    for arg in args:
        log += str(arg)
    _logger.error(log)

def generate_qr(url):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    qr_bytes = buf.getvalue()

    return base64.b64encode(qr_bytes).decode("utf-8")

def generate_UUID():
    return uuid.uuid4()

def get_datetime_date_to_epoch(my_date):
    # time.min represents the minimum time in the day, and the following line sets the epoch time to the beginning of the specified day
    return int(datetime.combine(my_date, time.min).timestamp())

def get_datetime_now_to_epoch(minutes_to_add):
    return int((datetime.now() + timedelta(minutes=minutes_to_add)).timestamp())
