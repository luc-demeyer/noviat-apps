# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    coda_id = fields.Many2one(
        comodel_name='account.coda', string='CODA Data File')
    coda_note = fields.Text('CODA Notes')
    coda_bank_account_id = fields.Many2one(
        comodel_name='coda.bank.account')

    def _automatic_reconcile(self, reconcile_note):
        if self.coda_bank_account_id:
            wiz = self.env['account.coda.import']
            reconcile_note = wiz._automatic_reconcile(
                self, reconcile_note)
        return super(AccountBankStatement, self
                     )._automatic_reconcile(reconcile_note)
