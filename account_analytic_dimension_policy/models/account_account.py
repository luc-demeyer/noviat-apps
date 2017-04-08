# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    analytic_dimension_policy = fields.Selection(
        string='Policy for analytic dimension',
        related='user_type.analytic_dimension_policy', readonly=True)
