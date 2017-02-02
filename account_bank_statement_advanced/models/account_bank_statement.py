# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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
