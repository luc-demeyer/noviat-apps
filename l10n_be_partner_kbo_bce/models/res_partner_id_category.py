# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, models


class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    @api.model
    def validate_l10n_be_partner_kbo_bce(self, id_number):
        failed = True
        kbo_bce_number = id_number.name
        supported_chars = '0-9.'
        pattern = re.compile('[^' + supported_chars + ']')
        if not pattern.findall(kbo_bce_number):
            kbo_bce_number = kbo_bce_number.replace('.', '')
            if len(kbo_bce_number) == 10:
                base = int(kbo_bce_number[:8])
                mod = base % 97
                if 97 - mod == int(kbo_bce_number[-2:]):
                    failed = False
        return failed
