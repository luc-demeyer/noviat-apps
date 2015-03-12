# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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

from openerp.osv import orm,fields
from openerp.tools.translate import _
from lxml import etree
import pickle
import logging
_logger = logging.getLogger(__name__)


class account_voucher_create(orm.TransientModel):
    """
    Create an account_voucher with lines selected by the end-user from a list of open AR/AP move lines.
    """
    _name = 'account.voucher.create'
    _description = 'account.voucher.create'

    def _get_stline(self, cr, uid, context=None):
        line = self.pool.get('account.bank.statement.line').browse(cr, uid, context['active_id'], context=context)
        stline = _('Amount') + ': %.2f' %line.amount
        stline += '\n' + _('Date') + ': ' + (line.val_date or line.date)
        stline += '\n' + _('Communication') + ': ' + (line.name)
        if getattr(line, 'counterparty_name', False):
            stline += '\n' + _('Counterparty Name') + ': ' + (line.counterparty_name)
        if getattr(line, 'counterparty_number', False):
            stline += ' - ' + _('Counterparty Number') + ': ' + (line.counterparty_number)
        if getattr(line, 'counterparty_bic', False):
            stline += ' (' + _('BIC') + ': ' + (line.counterparty_number) + ')'
        if getattr(line, 'payment_reference', False):
            stline += _('\nPayment Reference') + ': ' + (line.payment_reference)
        return stline

    def _get_move_line(self, cr, uid, context=None):
        # return matching move_line in case of matching amount, otherwise return nothing.
        move_line_ids = context['entries']
        move_lines = self.pool.get('account.move.line').browse(cr, uid, move_line_ids, context=context)
        st_line = self.pool.get('account.bank.statement.line').browse(cr, uid, context['active_id'], context=context)
        if st_line.amount > 0:
            matching_move_lines = filter(lambda x: x['debit'] == st_line.amount, move_lines)
        if st_line.amount < 0:
            matching_move_lines = filter(lambda x: x['credit'] == -st_line.amount, move_lines)
        if matching_move_lines:
            return [x['id'] for x in matching_move_lines]
        else:
            return []

    _columns = {
        'stline': fields.text('Bank Statement Line', readonly=True),
        'move_line_ids': fields.many2many('account.move.line', 'voucher_line_rel', 'move_line_id', 'voucher_line_id', 'Outstanding Transactions')
    }
    _defaults = {
        'stline': _get_stline,
        'move_line_ids': _get_move_line,
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_voucher_create, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if context and 'entries' in context:
            move_line_ids = context['entries']
            domain = "[('id', 'in', " + str(move_line_ids) + ')]'
            view_obj = etree.XML(res['arch'])
            for el in view_obj.iter():
                if el.tag == 'field' and el.attrib.get('name') == 'move_line_ids':
                    el.set('domain', domain)
            res['arch'] = etree.tostring(view_obj)
        #_logger.warn('fields_view_get, view arch=%s', res['arch'])
        return res

    def create_voucher(self, cr, uid, ids, context=None):
        #_logger.warn('%s, context=%s', self._name, context)
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        voucher_obj = self.pool.get('account.voucher')
        stline_obj = self.pool.get('account.bank.statement.line')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        wiz_data = self.browse(cr, uid, ids, context=context)[0]
        move_lines = wiz_data.move_line_ids    
        if not move_lines:
            return {'type': 'ir.actions.act_window_close'}
        partner_id = context.get('partner_id')
        if not partner_id:
            partner_ids = filter(lambda x: x, [x.partner_id and x.partner_id for x in move_lines])
            partner_ids = list(set(partner_ids))
            if not partner_ids:
                raise orm.except_orm(_('Unsupported Function !'),
                    _('Bank Statement Reconciliation with open transactions without Partner is currently not supported.'))
            elif len(partner_ids) > 1:
                raise orm.except_orm(_('Unsupported Function !'),
                    _('Bank Statement Reconciliation with open transactions of multiple distinct partners is currently not supported.'))
            else:
                partner_id = partner_ids[0].id
                stline_obj.write(cr, uid, context['active_id'], {'partner_id': partner_id})

        st_line = stline_obj.browse(cr, uid, context['active_id'], context=context)
        st_line_date = getattr(st_line, 'val_date', False) or st_line.date
        statement = st_line.statement_id
        journal = statement.journal_id
        st_name = statement.name
        if st_line.amount > 0:
            voucher_type = 'receipt'
            voucher_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_partner_receipt_form')
        else:
            voucher_type = 'payment'
            voucher_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_partner_payment_form')

        ttype = st_line.amount > 0 and 'receipt' or 'payment'
        company_currency_id = journal.company_id.currency_id.id
        currency_id = journal.currency.id
        if currency_id and currency_id != company_currency_id:
            multi_currency = True
        else:
            multi_currency = False
        context_multi_currency = context.copy()
        context_multi_currency.update({'date': st_line_date})

        line_cr_ids = []
        line_dr_ids = []
        amount_remaining = abs(st_line.amount)    
        for entry in move_lines:
            if entry.reconcile_partial_id:
                move_line = move_line_obj.browse(cr, uid, entry.id, context=context_multi_currency)
                amount_original = abs(move_line.amount_residual_currency)
            else:
                amount_original = entry.credit or entry.debit
                if multi_currency:
                    if entry.currency_id and entry.amount_currency:
                        amount_original = abs(entry.amount_currency)
                    else:
                        amount_original = currency_obj.compute(cr, uid, company_currency_id, currency_id, original_amount, context=context_multi_currency)
            if amount_remaining > 0:
                amount_voucher_line = min(amount_original, abs(amount_remaining))
                amount_remaining -= amount_voucher_line
            else:
                amount_voucher_line = 0.0
            voucher_line_vals = {
                'name':entry.name,
                'account_id': entry.account_id.id,
                'amount': amount_voucher_line,
                'reconcile': amount_voucher_line == amount_original,
                'type': entry.credit and 'dr' or 'cr',
                'move_line_id': entry.id,
            }
            if voucher_line_vals['type'] == 'cr':
                line_cr_ids += [(0, 0, voucher_line_vals)]
            else:
                line_dr_ids += [(0, 0, voucher_line_vals)]

        voucher_vals = { 
            'type': voucher_type,
            'name': st_line.name,
            'date': st_line_date,
            'journal_id': journal.id,
            'account_id': journal.default_credit_account_id.id,
            'line_cr_ids': line_cr_ids,
            'line_dr_ids': line_dr_ids,
            'pre_line': len(line_dr_ids) > 0 and True or False,
            'period_id': statement.period_id.id,
            'currency_id': currency_id,
            'company_id': journal.company_id.id,
            'state': 'draft',
            'amount': abs(st_line.amount),
            'reference': st_line.ref,
            'number': st_name + '/' + str(st_line.sequence),
            'partner_id': partner_id,
        }
        #_logger.warn('action_process, voucher_vals=%s, context=%s', voucher_vals, context)
        context['journal_id'] = journal.id # add journal to context for __get_payment_rate_currency method
        if line_cr_ids or line_dr_ids:
            voucher_id = voucher_obj.create(cr, uid, voucher_vals, context=context)
            stline_obj.write(cr, uid, [st_line.id], {'voucher_id': voucher_id})

        if voucher_id:
            act_voucher = {
                'name': _('Payment Reconciliation'),
                'res_id': voucher_id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.voucher',
                'view_id': [voucher_view[1]],
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
            act_voucher['context'] = dict(context, active_ids=ids, wizard_action=pickle.dumps(act_voucher))
            return act_voucher

    def create_move(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        statement_obj = self.pool.get('account.bank.statement')
        stline_obj = self.pool.get('account.bank.statement.line')
        st_line = stline_obj.browse(cr, uid, context['active_id'], context=context)
        statement = st_line.statement_id
        journal = statement.journal_id
        st_name = statement.name
        st_number = st_name
        st_line_number = statement_obj.get_next_st_line_number(cr, uid, st_number, st_line, context)
        company_currency_id = journal.company_id.currency_id.id
        move_id = stline_obj.create_move(cr, uid, st_line.id, company_currency_id, st_line_number, context=context)
        move_id = st_line.move_ids[0].id
        move_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_move_from_bank_form')
        act_move = {
            'name': _('Journal Entry'),
            'res_id': move_id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': [move_view[1]],
            'target': 'new',
            'context': dict(context, active_ids=ids),
            'type': 'ir.actions.act_window',
        }
        act_move['context'] = dict(context, active_ids=ids, wizard_action=pickle.dumps(act_move))
        return act_move

