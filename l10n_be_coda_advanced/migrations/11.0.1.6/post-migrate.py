# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    codas = env['account.coda'].search([])
    for coda in codas:
        data = coda.coda_data
        if not is_base64(data):
            coda.coda_data = base64.b64encode(data)
            _logger.warn(
                "CODA File %s (%s) has been repaired",
                coda.name, coda.coda_creation_date)


def is_base64(data):
    try:
        data = data.replace(b'\n', b'')
        return data == base64.b64encode(base64.b64decode(data))
    except Exception:
        return False
