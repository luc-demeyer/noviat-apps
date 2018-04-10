# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    name = fields.Char(translate=True)
