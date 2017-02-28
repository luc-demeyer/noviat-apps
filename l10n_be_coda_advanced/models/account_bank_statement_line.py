# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    coda_transaction_dict = fields.Char(
        string='CODA transaction details',
        help='JSON dictionary with the results of the CODA parsing')
