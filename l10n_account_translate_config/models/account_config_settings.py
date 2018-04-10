# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    module_l10n_account_translate_off = fields.Boolean(
        string='Monolingual General Accounts',
        help="If checked, the General Account will become "
             "a monolingual field.")
    module_l10n_multilang = fields.Boolean()
