# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BankStatementBalancePrint(models.TransientModel):
    _name = 'bank.statement.balance.print'
    _description = 'Bank Statement Balances Report'

    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Financial Journal(s)',
        domain=[('type', '=', 'bank')],
        help="Select here the Financial Journal(s) you want to include "
             "in your Bank Statement Balances Report.")
    date_balance = fields.Date(
        string='Date', required=True, default=fields.Date.today)

    @api.multi
    def balance_print(self):
        data = {
            'journal_ids': self.journal_ids.ids,
            'date_balance': self.date_balance,
        }
        return self.env.ref(
            'account_bank_statement_advanced.statement_balance_report_action'
        ).report_action(self, data=data)
