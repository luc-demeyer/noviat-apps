# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    # new fields
    statement_date = fields.Date(
        related='statement_id.date', string='Statement Date',
        readonly=True, store=True)
    val_date = fields.Date(
        string='Value Date')  # nl: valuta datum)
    journal_code = fields.Char(
        related='statement_id.journal_id.code',
        string='Journal Code', store=True, readonly=True)
    globalisation_id = fields.Many2one(
        comodel_name='account.bank.statement.line.global',
        string='Globalisation ID',
        readonly=True,
        help="Code to identify transactions belonging to the same "
             "globalisation level within a batch payment")
    globalisation_amount = fields.Monetary(
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
    moves_state = fields.Char(
        string='Moves State',
        compute='_compute_moves_state',
        readonly=True)
    # update existing fields
    state = fields.Selection(store=True)
    date = fields.Date(string='Entry Date')
    partner_id = fields.Many2one(
        domain=['|', ('parent_id', '=', False), ('is_company', '=', True)])

    @api.one
    @api.depends('journal_entry_ids')
    def _compute_reconcile_get(self):
        res = '-'
        """
        TODO:
        adapt logic for new aml fields:
            full_reconcile_id
            matched_debit_ids
            matched_credit_ids

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
        """
        self.reconcile_get = res

    @api.one
    @api.depends('journal_entry_ids')
    def _compute_moves_state(self):
        state = False
        moves = self.journal_entry_ids.mapped('move_id')
        states = moves.mapped('state')
        if states:
            state = any([x == 'draft' for x in states]) \
                and _('Unposted') or _('Posted')
        self.moves_state = state

    @api.onchange('currency_id', 'val_date', 'date')
    def _onchange_currency_id(self):
        if self.currency_id:
            self.amount_currency = self.statement_id.currency.with_context(
                date=self.val_date or self.date).compute(
                self.amount, self.currency_id)
        if not self.currency_id:
            self.amount_currency = 0.0

    @api.multi
    def unlink(self):
        glines = self.mapped('globalisation_id')
        todelete = glines.filtered(
            lambda gline: all(
                [stl_id in self.ids
                 for stl_id in gline.bank_statement_line_ids.ids])
        )
        todelete.unlink()
        return super().unlink()

    @api.multi
    def button_cancel_reconciliation(self):
        """
        remove the account_id from the st_line for manual reconciliation
        """
        for st_line in self:
            if st_line.account_id:
                st_line.account_id = False
        super().button_cancel_reconciliation()
        return True

    @api.multi
    def button_view_moves(self):
        self.ensure_one()
        moves = self.journal_entry_ids.mapped('move_id')
        act_move = {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', moves.ids)],
            'context': self._context,
            'type': 'ir.actions.act_window',
        }
        return act_move

    @api.model
    def _needaction_domain_get(self):
        res = super()._needaction_domain_get()
        res.append(('amount', '=', True))
        return res

    @api.multi
    def get_data_for_reconciliation_widget(self, excluded_ids=None):
        """
        Filter out zero amount lines.
        """
        lines = super().get_data_for_reconciliation_widget(
            excluded_ids=excluded_ids)
        lines = [l for l in lines if l['st_line']['amount'] != 0.0]
        return lines

    def _prepare_reconciliation_move(self, move_ref):
        data = super()._prepare_reconciliation_move(move_ref)
        if self.statement_id.accounting_date:
            data['date'] = self.statement_id.accounting_date
        return data
