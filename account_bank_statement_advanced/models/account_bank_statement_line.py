# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pickle

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    # new fields
    state = fields.Selection(
        related='statement_id.state', string='Statement State',
        readonly=True, store=True)
    statement_date = fields.Date(
        related='statement_id.date', string='Statement Date',
        readonly=True, store=True)
    val_date = fields.Date(
        string='Value Date',  # nl: valuta datum
        states={'confirm': [('readonly', True)]})
    journal_code = fields.Char(
        related='statement_id.journal_id.code',
        string='Journal', store=True, readonly=True)
    globalisation_id = fields.Many2one(
        'account.bank.statement.line.global',
        string='Globalisation ID',
        states={'confirm': [('readonly', True)]},
        help="Code to identify transactions belonging to the same "
        "globalisation level within a batch payment")
    globalisation_amount = fields.Float(
        related='globalisation_id.amount',
        string='Glob. Amount', readonly=True)
    counterparty_bic = fields.Char(
        string='Counterparty BIC', size=11,
        states={'confirm': [('readonly', True)]})
    counterparty_number = fields.Char(
        string='Counterparty Number',
        states={'confirm': [('readonly', True)]})
    counterparty_currency = fields.Char(
        string='Counterparty Currency', size=3,
        states={'confirm': [('readonly', True)]})
    payment_reference = fields.Char(
        string='Payment Reference', size=35,
        states={'confirm': [('readonly', True)]},
        help="Payment Reference. For SEPA (SCT or SDD) transactions, "
             "the EndToEndReference is recorded in this field.")
    creditor_reference_type = fields.Char(
        # To DO : change field to selection list
        string='Creditor Reference Type', size=35,
        states={'confirm': [('readonly', True)]},
        help="Creditor Reference Type. For SEPA (SCT) transactions, "
             "the <CdtrRefInf> type is recorded in this field."
             "\nE.g. 'BBA' for belgian structured communication "
             "(Code 'SCOR', Issuer 'BBA'")
    creditor_reference = fields.Char(
        'Creditor Reference',
        size=35,  # cf. pain.001.001.003 type="Max35Text"
        states={'confirm': [('readonly', True)]},
        help="Creditor Reference. For SEPA (SCT) transactions, "
             "the <CdtrRefInf> reference is recorded in this field.")
    reconcile_get = fields.Char(
        string='Reconciled', compute='_compute_reconcile_get', readonly=True)
    move_state = fields.Selection(
        string='Move State', related='journal_entry_id.state', readonly=True)

    # update existing fields
    date = fields.Date(string='Entry Date')
    partner_id = fields.Many2one(
        domain=['|', ('parent_id', '=', False), ('is_company', '=', True)])

    @api.one
    @api.depends('journal_entry_id')
    def _compute_reconcile_get(self):
        res = '-'
        move = self.journal_entry_id
        if move:
            reconciles = filter(lambda x: x.reconcile_id, move.line_id)
            rec_partials = filter(
                lambda x: x.reconcile_partial_id, move.line_id)
            rec_total = reduce(
                lambda y, t: (t.credit or 0.0) - (t.debit or 0.0) + y,
                reconciles + rec_partials, 0.0)
            if rec_total:
                res = '%.2f' % rec_total
                if rec_total != self.amount or rec_partials:
                    res += ' (!)'
        self.reconcile_get = res

    @api.onchange('currency_id', 'val_date', 'date')
    def _onchange_currency_id(self):
        if self.currency_id:
            self.amount_currency = self.statement_id.currency.with_context(
                date=self.val_date or self.date).compute(
                self.amount, self.currency_id)
        if not self.currency_id:
            self.amount_currency = 0.0

    @api.multi
    def cancel(self):
        """
        remove the account_id from the line for manual reconciliation
        """
        for line in self:
            if line.account_id:
                line.account_id = False
        super(AccountBankStatementLine, self).cancel()
        return True

    @api.multi
    def action_process(self):
        """
        TODO:
        add reconciliation/move logic for use in bank.statement.line list view
        """
        st_line = self[0]
        ctx = self._context.copy()
        ctx.update({
            'act_window_from_bank_statement': True,
            'active_id': st_line.id,
            'active_ids': [st_line.id],
            'statement_id': st_line.statement_id.id,
        })
        module = __name__.split('addons.')[1].split('.')[0]
        view = self.env.ref(
            '%s.view_move_from_bank_form' % module)
        act_move = {
            'name': _('Journal Entry'),
            'res_id': st_line.journal_entry_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': [view.id],
            'type': 'ir.actions.act_window',
        }
        act_move['context'] = dict(ctx, wizard_action=pickle.dumps(act_move))
        return act_move

    @api.multi
    def unlink(self):

        if self._context.get('block_statement_line_delete', False):
            raise UserError(
                _("Delete operation not allowed ! "
                  "Please go to the associated bank statement in order to "
                  "delete and/or modify this bank statement line"))

        # remove orphaned global lines
        if self._ids:
            self._cr.execute(
                "SELECT DISTINCT globalisation_id "
                "FROM account_bank_statement_line "
                "WHERE id IN %s AND globalisation_id IS NOT NULL",
                (self._ids,))
            g_ids = [x[0] for x in self._cr.fetchall()]
        else:
            g_ids = False
        res = super(AccountBankStatementLine, self).unlink()
        if g_ids:
            self._cr.execute(
                "SELECT DISTINCT globalisation_id "
                "FROM account_bank_statement_line "
                "WHERE globalisation_id IN %s", (tuple(g_ids),))
            g_ids2 = [x[0] for x in self._cr.fetchall()]
            todelete = [x for x in g_ids if x not in g_ids2]
            if todelete:
                self.pool['account.bank.statement.line.global'].unlink(
                    self._cr, self._uid, todelete, self._context)
        return res

    @api.model
    def create(self, vals):
        """
        This method can be dropped after acceptance by Odoo of
        - PR 8397
        - PR 8396
        Until these Pull Requests have been merged you should install the
        account_bank_statement.diff patch shipped with this module
        (cf. doc directory)
        """
        # cf. https://github.com/odoo/odoo/pull/8397
        if not vals.get('sequence'):
            lines = self.search(
                [('statement_id', '=', vals.get('statement_id'))],
                order='sequence desc', limit=1)
            if lines:
                seq = lines[0].sequence
            else:
                seq = 0
            vals['sequence'] = seq + 1
        # cf. https://github.com/odoo/odoo/pull/8396
        if not vals.get('name'):
            vals['name'] = '/'
        return super(AccountBankStatementLine, self).create(vals)

    @api.model
    def _needaction_domain_get(self):
        res = super(AccountBankStatementLine, self)._needaction_domain_get()
        res.append(('amount', '=', True))
        return res
