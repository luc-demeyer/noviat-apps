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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning
import pickle
import logging
_logger = logging.getLogger(__name__)


class account_bank_statement_line_global(models.Model):
    _name = 'account.bank.statement.line.global'
    _description = 'Batch Payment Info'
    _rec_name = 'code'

    name = fields.Char(
        string='OBI', required=True, default='/',
        help="Originator to Beneficiary Information")
    code = fields.Char(
        string='Code', required=True,
        default=lambda self: self.env['ir.sequence'].get(
            'account.bank.statement.line.global'))
    parent_id = fields.Many2one(
        'account.bank.statement.line.global',
        string='Parent Code', ondelete='cascade')
    child_ids = fields.One2many(
        'account.bank.statement.line.global', 'parent_id',
        string='Child Codes')
    type = fields.Selection([
        ('iso20022', 'ISO 20022'),
        ('coda', 'CODA'),
        ('manual', 'Manual'),
        ], string='Type', required=True)
    amount = fields.Float(
        string='Amount',
        digits_compute=dp.get_precision('Account'))
    payment_reference = fields.Char(
        string='Payment Reference',
        help="Payment Reference. For SEPA (SCT or SDD) transactions, "
             "the PaymentInformationIdentification "
             "is recorded in this field.")
    bank_statement_line_ids = fields.One2many(
        'account.bank.statement.line', 'globalisation_id',
        string='Bank Statement Lines')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            recs = self.search([('code', '=ilike', name)] + args, limit=limit)
            if not recs:
                recs = self.search(
                    [('name', operator, name)] + args, limit=limit)
            if not recs and len(name.split()) >= 2:
                # Separating code and name for searching
                # name can contain spaces
                operand1, operand2 = name.split(' ', 1)
                recs = self.search([
                    ('code', '=like', operand1), ('name', operator, operand2)
                    ] + args, limit=limit)
        else:
            recs = self.browse()
        return recs.name_get()


class account_bank_statement(models.Model):
    _inherit = 'account.bank.statement'

    fiscalyear_id = fields.Many2one(
        string='Fiscal Year', related='period_id.fiscalyear_id',
        store=True, readonly=True)

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

    @api.multi
    def write(self, vals):
        """
        Bypass statement line resequencing since replaced by sequencing
        via statement line create method.

        TODO:
        create PR to include this logic in the official addons since the
        logic in this module may break community modules that need
        to override the write method
        """
        return super(models.Model, self).write(vals)


class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.one
    def _get_reconcile(self):
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

    @api.one
    def _get_move(self):
        res = '-'
        move = self.journal_entry_id
        if move:
            field_dict = self.env['account.move'].fields_get(
                allfields=['state'])
            result_list = field_dict['state']['selection']
            res = filter(lambda x: x[0] == move.state, result_list)[0][1]
        self.move_get = res

    @api.one
    def _get_move_state(self):
        res = False
        move = self.journal_entry_id
        if move:
            res = move.state
        self.move_state = res

    # new fields
    state = fields.Selection(
        related='statement_id.state', string='Statement State',
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
    counterparty_name = fields.Char(
        string='Counterparty Name',
        states={'confirm': [('readonly', True)]})
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
        string='Reconciled', compute='_get_reconcile', readonly=True)
    move_get = fields.Char(string='Move', compute='_get_move', readonly=True)
    move_state = fields.Char(
        string='Move State', compute='_get_move_state', readonly=True)

    # update existing fields
    date = fields.Date(string='Entry Date')
    partner_id = fields.Many2one(
        domain=['|', ('parent_id', '=', False), ('is_company', '=', True)])

    @api.multi
    def action_cancel(self):
        """
        remove the account_id from the line for manual reconciliation
        """
        for line in self:
            if line.account_id:
                line.account_id = False
        self.cancel()
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
        view = self.env.ref(
            'account_bank_statement_advanced.view_move_from_bank_form')
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
            raise Warning(
                _("Delete operation not allowed ! "
                  "Please go to the associated bank statement in order to "
                  "delete and/or modify this bank statement line"))
        return super(account_bank_statement_line, self).unlink()

    @api.model
    def create(self, vals):
        if not vals.get('statement_id'):
            raise except_orm(
                _('Error !'),
                _("Please recalculate the statement balance first "
                  "via the 'Compute' button"))
        if not vals.get('sequence'):
            lines = self.search(
                [('statement_id', '=', vals['statement_id'])],
                order='sequence desc', limit=1)
            if lines:
                seq = lines[0].sequence
            else:
                seq = 0
            vals['sequence'] = seq + 1
        if not vals.get('name'):
            vals['name'] = '/'
        return super(account_bank_statement_line, self).create(vals)
