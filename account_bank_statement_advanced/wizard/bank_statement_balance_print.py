# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp import models, fields, api


class bank_statement_balance_print(models.TransientModel):
    _name = 'bank.statement.balance.print'
    _description = 'Bank Statement Balances Report'

    @api.model
    def _get_journals(self):
        return self.env['account.journal'].search([('type', '=', 'bank')])

    journal_ids = fields.Many2many(
        'account.journal', string='Financial Journal(s)',
        domain=[('type', '=', 'bank')], default=_get_journals,
        help="Select here the Financial Journal(s) you want to include "
             "in your Bank Statement Balances Report.")
    date_balance = fields.Date(
        string='Date', required=True, default=time.strftime('%Y-%m-%d'))

    @api.multi
    def balance_print(self):
        return self.env['report'].get_action(
            self, 'account_bank_statement_advanced.report_statement_balances')
