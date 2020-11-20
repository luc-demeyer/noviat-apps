# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo import api, fields, models, _


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    coda_id = fields.Many2one(
        comodel_name='account.coda', string='CODA Data File')
    coda_note = fields.Text('CODA Notes')
    coda_bank_account_id = fields.Many2one(
        comodel_name='coda.bank.account')

    @api.multi
    def button_confirm_bank(self):
        """
        Some of the function in this method are handled (differently) by the
        CODA processing hence we bypass those here.
        """
        coda_statements = self.filtered(lambda r: r.coda_id)
        non_coda_statements = self - coda_statements
        super(AccountBankStatement, non_coda_statements).button_confirm_bank()

        coda_statements._balance_check()
        coda_statements = coda_statements.filtered(
            lambda r: r.state == 'open')
        moves = coda_statements.mapped('line_ids.journal_entry_ids.move_id')
        unposted = moves.filtered(lambda r: r.state == 'draft')
        unposted.post()
        for statement in coda_statements:
            statement.message_post(
                body=_('Statement %s confirmed, journal items were created.'
                       ) % (statement.name,))
        coda_statements.write({
            'state': 'confirm',
            'date_done': time.strftime("%Y-%m-%d %H:%M:%S")})
        return True

    def _automatic_reconcile(self, reconcile_note='', st_lines=None):
        self.ensure_one()
        if self.coda_bank_account_id:
            wiz = self.env['account.coda.import']
            reconcile_note = wiz._automatic_reconcile(
                self, reconcile_note=reconcile_note, st_lines=st_lines)
            return reconcile_note
        return super()._automatic_reconcile(
            reconcile_note=reconcile_note, st_lines=st_lines)
