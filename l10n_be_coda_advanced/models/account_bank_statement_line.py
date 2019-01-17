# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    coda_transaction_dict = fields.Char(
        string='CODA transaction details',
        help='JSON dictionary with the results of the CODA parsing')

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        """
        Allow zero amount transactions
        Such lines are used in CODA files to give additional information).
        """
        if not self.coda_transaction_dict:
            super(AccountBankStatementLine, self)._check_amount()
