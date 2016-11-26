# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class account_fiscal_position(models.Model):
    _inherit = 'account.fiscal.position'

    name = fields.Char(translate=True)
    note = fields.Text(translate=True)
