# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    coda_id = fields.Many2one(
        'account.coda', string='CODA Data File')
    coda_note = fields.Text('CODA Notes')
