# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_l10n_account_translate_off = fields.Boolean(
        string='Monolingual General Accounts',
        help="If checked, the General Account will become "
             "a monolingual field.")
    module_l10n_multilang = fields.Boolean()
