# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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

from openerp import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    period_id = fields.Many2one(domain=[('special', '=', False)])
    fiscalyear_id = fields.Many2one(
        string='Fiscal Year', related='period_id.fiscalyear_id',
        store=True, readonly=True)
    all_lines_reconciled = fields.Boolean(compute='_all_lines_reconciled')

    @api.one
    @api.depends('line_ids')
    def _all_lines_reconciled(self):
        """
        Replacement of this method without inherit.

        Standard account module logic:
        all([line.journal_entry_id.id or line.account_id.id
             for line in statement.line_ids])
        """
        self.all_lines_reconciled = True
        for line in self.line_ids:
            if line.amount and not line.journal_entry_id:
                self.all_lines_reconciled = False
                break

    def init(self, cr):
        cr.execute("""
    ALTER TABLE account_bank_statement
      DROP CONSTRAINT IF EXISTS account_bank_statement_name_uniq;
    DROP INDEX IF EXISTS account_bank_statement_name_non_slash_uniq;
    CREATE UNIQUE INDEX account_bank_statement_name_non_slash_uniq ON
      account_bank_statement(name, journal_id, fiscalyear_id, company_id)
      WHERE name !='/';
        """)

    @api.multi
    def button_cancel(self):
        """
        Replace the account module button_cancel to allow
        cancel statements while preserving associated moves.
        """
        self.state = 'draft'
        return True
