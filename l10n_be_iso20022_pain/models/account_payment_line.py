# -*- coding: utf-8 -*-
# Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    communication_type = fields.Selection(
        selection_add=[('bba', 'BBA Structured Communication')])
