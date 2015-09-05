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

from openerp.osv import fields,orm
from openerp.tools.translate import _
import pickle
import logging
_logger = logging.getLogger(__name__)


class account_bank_statement_line(orm.Model):
    _inherit = 'account.bank.statement.line'

    def _get_reconcile(self, cr, uid, ids, name, args, context=None):
        voucher_obj = self.pool.get('account.voucher')
        reconcile_obj = self.pool.get('account.move.reconcile')
        res = {}
        for st_line in self.browse(cr, uid, ids, context=context):
            if st_line.voucher_id:
                if st_line.voucher_id.state == 'posted':
                    if st_line.voucher_id.paid:
                        res[st_line.id] = '%.2f' %st_line.amount
                    else:
                        reconciles = filter(lambda x: x.reconcile_id, st_line.voucher_id.move_ids)
                        rec_partials = filter(lambda x: x.reconcile_partial_id, st_line.voucher_id.move_ids)
                        rec_total = reduce(lambda y,t: (t.credit or 0.0) - (t.debit or 0.0) + y, reconciles + rec_partials, 0.0)
                        res[st_line.id] = '%.2f' %rec_total
                        if rec_total != st_line.amount or rec_partials:
                            res[st_line.id] += ' (!)'
                else:
                    res[st_line.id] = _('To be Checked')
            #elif st_line.move_ids and st_line.account_id.type in ['payable', 'receivable']:
            elif st_line.move_ids and st_line.account_id.reconcile:
                move=st_line.move_ids[0] # only single move linked to single statement line supported
                if move.state == 'posted':
                    reconciles = filter(lambda x: x.reconcile_id, move.line_id)  
                    rec_partials = filter(lambda x: x.reconcile_partial_id, move.line_id)  
                    rec_total = reduce(lambda y,t: (t.credit or 0.0) - (t.debit or 0.0) + y, reconciles + rec_partials, 0.0)
                    res[st_line.id] = '%.2f' %rec_total
                    if rec_total != st_line.amount or rec_partials:
                        res[st_line.id] += ' (!)'
                else:
                    res[st_line.id] = _('To be Checked')
            else:
                res[st_line.id] = '-'
        return res

    def _get_move(self, cr, uid, ids, name, args, context=None):
        res = {}
        for st_line in self.browse(cr, uid, ids, context=context):
            if st_line.move_ids:
                if len(st_line.move_ids) > 1:
                    raise orm.except_orm(_('Unsupported Function !'),
                            _('Multiple Account Moves linked to a single Bank Statement Line is currently not supported.' \
                              'Bank Statement "%s", Bank Statement Line "%s"') % (st_line.statement_id.name, st_line.ref or st_line.sequence) )               
                move_state = st_line.move_ids[0].state
                if name == 'move_get':
                    field_dict = self.pool.get('account.move').fields_get(cr, uid, allfields=['state'], context=context)
                    result_list = field_dict['state']['selection']
                    res[st_line.id] = filter(lambda x: x[0] == move_state, result_list)[0][1]
                else:
                    res[st_line.id] = move_state
            else:
                if name == 'move_get':
                    res[st_line.id] = '-'
                else:
                    res[st_line.id] = False
        return res

    _columns = {
        'voucher_id': fields.many2one('account.voucher', 'Payment', readonly=True),
        'reconcile_get': fields.function(_get_reconcile, method=True, string='Reconciled', type='char', readonly=True),
        'voucher_state': fields.related('voucher_id', 'state', type='char', relation='account.voucher',
            string='Voucher State', readonly=True),     
        'move_get': fields.function(_get_move, method=True, string='Move', type='char', readonly=True),
        'move_state': fields.function(_get_move, method=True, string='Move State', type='char', readonly=True),
    }

    def create_move(self, cr, uid, st_line_id, company_currency_id, st_line_number, context=None):
        """
        This method has been copied from the account module 'create_move_from_st_line' method on the bank statement
        and adapted as follows:
        - runs from Bank Statement Line in stead of Bank Statement
        - the generated move is not posted, thereby allowing the user to make modifications before posting
        """
        if context is None:
            context = {}
        res_currency_obj = self.pool.get('res.currency')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        st_obj = self.pool.get('account.bank.statement')
        st_line = self.browse(cr, uid, st_line_id, context=context)
        st = st_line.statement_id
        st_line_date = getattr(st_line, 'val_date', False) or st_line.date

        context_create_move = context.copy()
        context_create_move.update({'date': st_line_date})

        if st_line.move_ids:
            if len(st_line.move_ids) > 1:
                raise orm.except_orm(_('Unsupported Function !'),
                        _('Multiple Account Moves linked to a single Bank Statement Line is currently not supported.' \
                          'Bank Statement "%s", Bank Statement Line "%s"') % (st_line.statement_id.name, st_line_number) )               
            move_id = st_line.move_ids[0].id
        else:
            move_vals = st_obj._prepare_move(cr, uid, st_line, st_line_number, context=context_create_move)
            move_id = account_move_obj.create(cr, uid, move_vals, context=context_create_move)
            self.write(cr, uid, [st_line.id], {'move_ids': [(4, move_id, False)]})

            # Remark: 
            # The following code block is for the "Outgoing Currency Rate = Average" setting
            # No testing has been performed on the correct functioning of this setting in combination
            # with the 'account_bank_statement_voucher' module
            acc_cur = ((st_line.amount<=0) and st.journal_id.default_debit_account_id) or st_line.account_id
            context_create_move.update({
                    'res.currency.compute.account': acc_cur,
                })
            
            if st.currency.id != company_currency_id:
                amount = res_currency_obj.compute(cr, uid, st.currency.id,
                        company_currency_id, st_line.amount, context=context_create_move)
            else:
                amount = st_line.amount

            # create move on statement line account
            bank_move_vals = st_obj._prepare_bank_move_line(cr, uid, st_line, move_id, amount, company_currency_id, context=context_create_move)
            move_line_id = account_move_line_obj.create(cr, uid, bank_move_vals, context=context_create_move)

            # create move on bank journal account
            if 'tax_code_id' in context_create_move:
                del context_create_move['tax_code_id']
            counterpart_move_vals = st_obj._prepare_counterpart_move_line(cr, uid, st_line, move_id,
                amount, company_currency_id, context=context_create_move)
            account_move_line_obj.create(cr, uid, counterpart_move_vals, context=context_create_move)

        """
        for line in account_move_line_obj.browse(cr, uid, 
            [x.id for x in account_move_obj.browse(cr, uid, move_id, context=context).line_id], context=context):
            if line.state != 'valid':
                raise orm.except_orm(_('Error !'), _('Journal Item "%s" is not valid') % line.name)
        """

        return move_id

    def action_process(self, cr, uid, ids, context=None):
        #_logger.warn('%s, action_process, context = %s', self._name, context)
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        voucher_obj = self.pool.get('account.voucher')
        move_line_obj = self.pool.get('account.move.line')
        partner_bank_obj = self.pool.get('res.partner.bank')
        statement_obj = self.pool.get('account.bank.statement')
        cur_obj = self.pool.get('res.currency')

        for st_line in self.browse(cr, uid, ids, context=context):
            if not st_line.amount:
                raise orm.except_orm(_('Warning !'), _('Please fill in the transaction amount.'))               
            statement = st_line.statement_id
            st_line_date = getattr(st_line, 'val_date', False) or st_line.date
            journal = statement.journal_id
            company = journal.company_id
            context.update({
                'act_window_from_bank_statement': True,
                'active_id' : st_line.id,
                'active_ids' : [st_line.id],
                'statement_id': st_line.statement_id.id,
                })

            # Check/Update Partner Records
            if st_line.partner_id and hasattr(st_line, 'counterparty_number') and st_line.counterparty_number \
                and not context.get('update_partner_record') == 'done' and st_line.account_id.type in ['receivable', 'payable']:
                counterparty_number = st_line.counterparty_number
                partner = st_line.partner_id
                partner_bank_ids = partner_bank_obj.search(
                    cr,uid,
                    [('acc_number','=', counterparty_number),
                     ('partner_id','=', partner.id)],
                    order='id')
                partner_banks = partner_bank_obj.browse(cr, uid, partner_bank_ids, context=context)
                if len(partner_bank_ids) != 1:
                    ctx = context.copy()
                    info = ''
                    # clean up partner bank duplicates
                    if len(partner_bank_ids) > 1 or (len(partner_bank_ids) == 1 and partner_banks[0].partner_id.id != partner.id):                       
                        unlink_ids = [x.id for x in filter(lambda x: x.partner_id != partner, partner_banks)]
                        if unlink_ids:
                            info += _("The Bank Account Number '%s' has been found on the following Partner Records: \n") %counterparty_number
                            info += ', '.join([x.partner_id.name for x in partner_banks]) 
                            info += _("\nUpdate Partner Records (only the entry for partner '%s' will be preserved) ?") %partner.name
                        diff_ids = set(partner_bank_ids) - set(unlink_ids)
                        if len(diff_ids) > 1:
                            info += _("Duplicate Bank Account Numbers have been found for Partner Record '%s (id:%s)' \n") %(partner.name, partner.id)
                            info += _("The duplicates will be removed. \n")
                            unlink_ids += list(diff_ids)[:-1]
                        ctx.update({'info': info, 'partner_bank_unlink_ids': unlink_ids}) 
                    # add partner bank
                    if not partner_bank_ids or (len(partner_bank_ids) == 1 and partner_banks[0].partner_id.id != partner.id):
                        if info:
                            info += "\n\n"
                        info += _("The Bank Account Number '%s' has not been defined for Partner '%s'.") %(counterparty_number, partner.name)
                        info += _("\nUpdate Partner Record ?")
                        ctx.update({'info': info, 'partner_bank_create': True}) 
                    update_partner_obj = self.pool.get('update.partner.record')
                    result = mod_obj._get_id(cr, uid, 'account_bank_statement_voucher', 'action_update_partner_record')
                    id = mod_obj.read(cr, uid, [result], ['res_id'])[0]['res_id']
                    act_partner_update = act_obj.read(cr, uid, [id])[0]
                    act_partner_update.update({'context': ctx, 'nodestroy': True,})
                    return act_partner_update

            # Check/Set Bank Statement Name
            st_name = statement.name
            if st_name == '/':
                st_obj = self.pool.get('account.bank.statement')
                if journal.sequence_id:
                    c = {'fiscalyear_id': statement.period_id.fiscalyear_id.id}
                    st_name = self.pool.get('ir.sequence').next_by_id(cr, uid, journal.sequence_id.id, context=c)
                else:
                    raise orm.except_orm(_('Error'),
                        _("Please define an Entry Sequence on your Bank Journal or fill in the Bank Statement Name !"))
                st_obj.write(cr, uid, [statement.id], {'name': st_name}, context=context)

            voucher_id = False

            if st_line.account_id.type in ['receivable', 'payable']:
                partner_id = st_line.partner_id and st_line.partner_id.id or False
                partner_clause = partner_id and " AND aml.partner_id = %s " %partner_id or ''
                query = "SELECT aml.id, aml.date, aml.account_id, COALESCE(aml.partner_id, 0), " \
                        "COALESCE(aml.debit, 0.0) AS debit, COALESCE(aml.credit, 0.0) AS credit, " \
                        "COALESCE(aml.currency_id, 0) AS currency_id, COALESCE(aml.amount_currency, 0.0) AS amount_currency, " \
                        "COALESCE(aml.reconcile_partial_id, 0) AS reconcile_partial_id, am.name AS move_name " \
                        "FROM account_move_line aml " \
                        "INNER JOIN account_move am ON aml.move_id = am.id " \
                        "INNER JOIN account_account aa ON aml.account_id = aa.id " \
                        "WHERE aml.state = 'valid' AND aml.reconcile_id IS NULL AND aa.type in ('receivable', 'payable') " \
                        "AND aml.statement_id IS DISTINCT FROM %s AND aml.company_id = %s " %(st_line.statement_id.id, company.id) \
                         + partner_clause + \
                        "ORDER BY aml.date, aml.id" 

                if st_line.amount > 0:
                    voucher_type = 'receipt'
                    voucher_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_partner_receipt_form')
                else:
                    voucher_type = 'payment'
                    voucher_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_partner_payment_form')

                if not st_line.voucher_id and not st_line.move_ids:
                    cr.execute(query)
                    all_entries = cr.dictfetchall()
                    #remove partially reconciled receivables/payables
                    def remove_filter(entry):
                        if entry['reconcile_partial_id']:
                            if voucher_type == 'receipt' and entry['credit']:
                                return True
                            elif voucher_type == 'payment' and entry['debit']:
                                return True
                        return False  
                    removes = filter(remove_filter, all_entries)
                    remove_ids = [x['id'] for x in removes]
                    entries = filter(lambda x: x['id'] not in remove_ids, all_entries)

                    if not entries:
                        # call wizard to allow creation of accounting move without reconciliation
                        result = mod_obj._get_id(cr, uid, 'account_bank_statement_voucher', 'action_account_move_create')
                        id = mod_obj.read(cr, uid, [result], ['res_id'])[0]['res_id']
                        act_move_create = act_obj.read(cr, uid, [id])[0]
                        act_move_create.update({'context': context, 'nodestroy': True,})
                        return act_move_create
                    
                    if len(entries) > 1:
                        # call wizard to select move lines from list of outstanding transactions
                        ctx_voucher_create = dict(context, entries=[x['id'] for x in entries],
                            partner_id=partner_id, company_id=company.id)
                        act_voucher_create = {
                            'name': _('Select Transactions'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'account.voucher.create',
                            'target': 'new',
                            'nodestroy': True,
                            'context': ctx_voucher_create,
                            'type': 'ir.actions.act_window',
                        }                  
                        return act_voucher_create

                    company_currency_id = journal.company_id.currency_id.id
                    currency_id = journal.currency.id or company_currency_id
                    if currency_id != company_currency_id:
                        multi_currency = True
                    else:
                        multi_currency = False
                    context_multi_currency = context.copy()
                    context_multi_currency.update({'date': getattr(st_line, 'val_date', False) or st_line.date})

                    line_cr_ids = []
                    line_dr_ids = []
                    amount_remaining = abs(st_line.amount)
                    for entry in entries:
                        # To DO : reorder entries if exact match is found and put matching record on top
                        if entry['reconcile_partial_id']:
                            move_line = move_line_obj.browse(cr, uid, entry['id'], context=context_multi_currency)
                            amount_original = abs(move_line.amount_residual_currency)
                        else:
                            amount_original = entry['credit'] or entry['debit']
                            if multi_currency:
                                if entry['currency_id'] and entry['amount_currency']:
                                    amount_original = abs(entry['amount_currency'])
                                else:
                                    amount_original = cur_obj.compute(cr, uid, company_currency_id, currency_id, original_amount, context=context_multi_currency)
                        if amount_remaining > 0:
                            amount_voucher_line = min(amount_original, abs(amount_remaining))
                            amount_remaining -= amount_voucher_line
                        else:
                            amount_voucher_line = 0.0
                        voucher_line_vals = {
                            'name':entry['move_name'],
                            'account_id': entry['account_id'],
                            'amount': amount_voucher_line,
                            'reconcile': amount_voucher_line == amount_original,
                            'type': entry['credit'] and 'dr' or 'cr',
                            'move_line_id': entry['id'],
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
                        'actvie': False,
                        'amount': abs(st_line.amount),
                        'reference': st_line.ref,
                        'number': st_name + '/' + str(st_line.sequence),
                        'partner_id': st_line.partner_id.id,
                    }
                    #_logger.warn('action_process, voucher_vals=%s, context=%s', voucher_vals, context)
                    if line_cr_ids or line_dr_ids:
                        voucher_id = voucher_obj.create(cr, uid, voucher_vals, context=dict(context, journal_id=journal.id))
                        self.write(cr, uid, [st_line.id], {'voucher_id': voucher_id})

                else:
                    voucher_id = st_line.voucher_id.id

            if voucher_id:
                voucher = voucher_obj.browse(cr, uid, voucher_id, context=context)
                # when migrating from the standard 'green/red bullet' bank statement, the voucher number is not present
                if not voucher.number:
                    voucher_obj.write(cr, uid, voucher_id, {'number': st_name + '/' + str(st_line.sequence)})

                if context.get('destroy_wizard_form'):
                    nodestroy = False
                else:
                    nodestroy = True
                act_voucher = {
                    'name': _('Payment Reconciliation'),
                    'res_id': voucher_id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.voucher',
                    'view_id': [voucher_view[1]],
                    'nodestroy': nodestroy,
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                }
                act_voucher['context'] = dict(context, wizard_action=pickle.dumps(act_voucher))
                return act_voucher
            # create move record if reconciliation via voucher didn't succeed    
            else:            
                """
                Create accounting moves from 
                - non-AR/AP accounts
                - AR/AP accounts without partner_id
                """
                if not st_line.move_ids:
                    st_number = st_name
                    st_line_number = statement_obj.get_next_st_line_number(cr, uid, st_number, st_line, context)
                    company_currency_id = journal.company_id.currency_id.id
                    move_id = self.create_move(cr, uid, st_line.id, company_currency_id, st_line_number, context=context)
                else:
                    if len(st_line.move_ids) > 1:
                        raise orm.except_orm(_('Unsupported Function !'),
                                _('Multiple Account Moves linked to a single Bank Statement Line is currently not supported.' \
                                  'Bank Statement "%s", Bank Statement Line "%s"') % (st_line.statement_id.name, st_line_number) )               
                    move_id = st_line.move_ids[0].id
                move_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_move_from_bank_form')
                act_move = {
                    'name': _('Journal Entry'),
                    'res_id': move_id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': [move_view[1]],
                    'nodestroy': True,
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                }
                act_move['context'] = dict(context, wizard_action=pickle.dumps(act_move))
                return act_move

    def action_undo(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')
        move_obj = self.pool.get('account.move')
        for st_line in self.browse(cr, uid, ids, context=context):       
            if st_line.voucher_id:
                voucher_obj.unlink(cr, uid, [st_line.voucher_id.id])
            else:
                if st_line.move_ids:
                    move_obj.unlink(cr, uid, [x.id for x in st_line.move_ids], context=context)
        return True

    def onchange_type(self, cr, uid, line_ids, partner_id, type, context=None):
        res = {'value': {}}
        if context is None:
            context = {}

        # change by Noviat: always retrieve AR/AP account from partner record when changing type
        if not partner_id or type not in ['supplier', 'customer']:
            return res
        
        st_lines = self.browse(cr, uid, line_ids, context)
        for st_line in st_lines:
            """ block changes to bank statement lines with an associated account.move  """
            if st_line.move_ids: 
                raise orm.except_orm(_('Invalid action !'), 
                    _("You cannot change the 'Type' field of a bank statement line with an associated Accounting Move!"   \
                      "\nPlease remove first this Move."))
            elif st_line.voucher_id:
                raise orm.except_orm(_('Invalid action !'), 
                    _("You cannot change the 'Type' field of a bank statement line with an associated Reconciliation object!"   \
                      "\nPlease remove first this Reconciliation object."))
        account_id = False
        obj_partner = self.pool.get('res.partner')
        part = obj_partner.browse(cr, uid, partner_id, context=context)
        if type == 'supplier':
            account_id = part.property_account_payable.id
        elif type == 'customer':
            account_id = part.property_account_receivable.id
        res['value']['account_id'] = account_id
        return res

    def write(self, cr, uid, ids, vals, context={}):   
        #_logger.warn('write, vals=%s, context=%s', vals, context)
        voucher_obj = self.pool.get('account.voucher')
        move_line_obj = self.pool.get('account.move.line')       
        if isinstance(ids, (int, long)):
            ids = [ids]

        for st_line in self.browse(cr, uid, ids, context):
            """ block changes to bank statement lines with an associated account_move or account_voucher """
            if st_line.move_ids or st_line.voucher_id:
                for field in ['ref', 'partner_id', 'type', 'account_id', 'amount', 'analytic_account_id']:
                    if field in vals.keys():
                        old_val = getattr(st_line, field)
                        if field in ['partner_id', 'account_id', 'analytic_account_id']:
                            old_val = old_val.id
                        new_val = vals[field]
                        if old_val != new_val:
                            st = st_line.statement_id
                            if st_line.move_ids:
                                raise orm.except_orm(_('Invalid action !'), 
                                    _("You cannot change the '%s' field of a bank statement line with an associated Accounting Move!"   \
                                      "\nPlease remove first this Move."  \
                                      "\nCf. Bank Statement '%s', Transaction Reference '%s'.") %(field, st.name, st_line.ref or st_line.name))
                            elif st_line.voucher_id:
                                raise orm.except_orm(_('Invalid action !'), 
                                    _("You cannot change the '%s' field of a bank statement line with an associated Reconciliation object!"   \
                                      "\nPlease remove first this Reconciliation object."  \
                                      "\nCf. Bank Statement '%s', Transaction Reference '%s'.") %(field, st.name, st_line.ref or st_line.name))

            """ Avoid 'orphaned' vouchers """
            if vals.has_key('voucher_id'):
                old_voucher_id = st_line.voucher_id.id
                new_voucher_id = vals['voucher_id']
                if old_voucher_id and old_voucher_id != new_voucher_id:
                        voucher_obj.unlink(cr, uid, [old_voucher_id])

        return super(account_bank_statement_line, self).write(cr, uid, ids, vals, context)
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for st_line in self.browse(cr, uid, ids, context):
            """ block deletes of bank statement lines with an associated account.move or account_voucher """
            if st_line.move_ids or st_line.voucher_id:
                st = st_line.statement_id
                if st_line.move_ids:
                    raise orm.except_orm(_('Invalid action !'), 
                        _("You cannot delete a bank statement line with an associated Accounting Move!"   \
                          "\nPlease remove first this Move."  \
                          "\nCf. Bank Statement '%s', Transaction Reference '%s'.") %(st.name, st_line.ref or st_line.name))
                elif st_line.voucher_id:
                    raise orm.except_orm(_('Invalid action !'), 
                        _("You cannot delete a bank statement line with an associated Reconciliation object!"   \
                          "\nPlease remove first this Reconciliation object."  \
                          "\nCf. Bank Statement '%s', Transaction Reference '%s'.") %(st.name, st_line.ref or st_line.name))
        return super(account_bank_statement_line, self).unlink(cr, uid, ids, context=context)


class account_bank_statement(orm.Model):
    _inherit = 'account.bank.statement'   

    def _end_balance(self, cr, uid, ids, name, attr, context=None):
        """ 
        Change balance calculation for draft statements. 
        This is required since this module changes the voucher behaviour by generating moves linked to the bank statement lines. 
        """
        res = super(account_bank_statement, self)._end_balance(cr, uid, ids, name, attr, context=context)
        for st in self.browse(cr, uid, ids, context=context):
            if st.state == 'draft' and st.journal_id.type == 'bank':
                res[st.id] = st.balance_start
                for line in st.line_ids:
                    res[st.id] += line.amount
                res[st.id] = round(res[st.id], 2)
        return res

    _columns = {
        'period_id': fields.many2one('account.period', 'Period', required=True,
            domain=[('special', '=', False)],
            states={'confirm':[('readonly', True)]}),
        'move_line_ids': fields.one2many('account.move.line', 'statement_id', 'Entry lines', readonly=True),
        'balance_end': fields.function(_end_balance, method=True, string='Balance', store=True,     
            help="Closing balance based on Starting Balance and Cash Transactions"),
        'state': fields.selection([('draft', 'Draft'), # Change 'New' -> 'Draft'
                                   ('open','Open'), # used by cash statements
                                   ('confirm', 'Closed')],
                                   'State', required=True, readonly="1",
                                   help='It is recommend to keep a statement in the \'Draft\' state '
                                        'until all transactions have been reviewed and reconciled.'),
    }

    def _get_counter_part_account(self, cr, uid, st_line, context=None):
        if not context:
            context = {}
        # we don't support different debit & credit accounts when generating moves from a bank statement line
        if context.get('act_window_from_bank_statement'):
            journal = st_line.statement_id.journal_id
            if journal.default_credit_account_id != journal.default_debit_account_id:
                raise orm.except_orm(_("Unsupported Function !"),
                    _("The Debit Account of your Bank Journal must be equal to the Credit Account."))
        return super(account_bank_statement, self)._get_counter_part_account(cr, uid, st_line, context)

    def _prepare_move(self, cr, uid, st_line, st_line_number, context=None):
        vals = super(account_bank_statement, self)._prepare_move(cr, uid, st_line, st_line_number, context)
        if not context: context={}
        if context.get('date'):
            vals['date'] = context['date']
        if not vals.get('ref'):
             vals['ref'] = st_line_number
        return vals

    def _prepare_move_line_vals(self, cr, uid, st_line, move_id, debit, credit, currency_id = False,
                amount_currency= False, account_id = False, analytic_id = False,
                partner_id = False, context=None):
        vals = super(account_bank_statement, self)._prepare_move_line_vals(cr, uid, st_line, move_id, debit, credit, currency_id,
            amount_currency, account_id, analytic_id, partner_id, context)
        if not context: context = {}
        if context.get('date'):
            vals['date'] = context['date']
        if context.get('tax_code_id'):
            vals['tax_code_id'] = context['tax_code_id']
            vals['tax_amount'] = vals['debit'] or vals['credit']
        return vals

    def button_confirm_bank(self, cr, uid, ids, context=None):
        """
        Replace account module 'button_confirm_bank' method to call bank_statement_line create_move method
        Since the method is replaced, also the logic in the inherited 'account_bank_statement_extensions' module is included.
        """
        obj_seq = self.pool.get('ir.sequence')
        if context is None:
            context = {}

        for st in self.browse(cr, uid, ids, context=context):
            j_type = st.journal_id.type
            company_currency_id = st.journal_id.company_id.currency_id.id
            if not self.check_status_condition(cr, uid, st.state, journal_type=j_type):
                continue

            self.balance_check(cr, uid, st.id, journal_type=j_type, context=context)
            if (not st.journal_id.default_credit_account_id) \
                    or (not st.journal_id.default_debit_account_id):
                raise orm.except_orm(_('Configuration Error !'),
                        _('Please verify that an account is defined in the journal.'))

            if not st.name == '/':
                st_number = st.name
            else:
                c = {'fiscalyear_id': st.period_id.fiscalyear_id.id}
                if st.journal_id.sequence_id:
                    st_number = obj_seq.next_by_id(cr, uid, st.journal_id.sequence_id.id, context=c)
                else:
                    st_number = obj_seq.next_by_code(cr, uid, 'account.bank.statement', context=c)

            for line in st.move_line_ids:
                if line.state != 'valid':
                    raise orm.except_orm(_('Error !'),
                            _('The account entries lines are not in valid state.'))
            for st_line in st.line_ids:
                if st_line.analytic_account_id:
                    if not st.journal_id.analytic_journal_id:
                        raise orm.except_orm(_('No Analytic Journal !'),_("You have to define an analytic journal on the '%s' journal!") % (st.journal_id.name,))
                if not st_line.amount:
                    continue
                st_line_number = self.get_next_st_line_number(cr, uid, st_number, st_line, context)
                if j_type == 'bank':
                    if st_line.voucher_id:
                        voucher = self.pool.get('account.voucher').browse(cr, uid, st_line.voucher_id.id)
                        if voucher.state != 'posted':
                            raise orm.except_orm(_('Error !'),
                                _('The reconciliation for line %s (Communication: %s) has not been completed.') 
                                % (st_line.sequence, st_line.name + (st_line.ref and (', ' + _('Reference') + ': ' + st_line.ref) or '')))
                    move_id = self.pool.get('account.bank.statement.line').create_move(cr, uid, st_line.id, company_currency_id, st_line_number, context)
                    self.pool.get('account.move').post(cr, uid, [move_id], context=context)
                else:
                    self.create_move_from_st_line(cr, uid, st_line.id, company_currency_id, st_line_number, context)

            self.write(cr, uid, [st.id], {
                    'name': st_number,
                    #'balance_end_real': st.balance_end  # balance_end_real must correspond with digital or paper bank statement and should not be set by calculated field !
            }, context=context)
            self.log(cr, uid, st.id, _('Statement %s is confirmed, journal items are created.') % (st_number,))
        return self.write(cr, uid, ids, {'state':'confirm'}, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        """
        Replace the account module button_cancel to allow cancelling statements while preserving associated moves.
        Those moves will be removed when deleting the associated bank statement line.
        """
        done = []
        for st in self.browse(cr, uid, ids, context=context):
            if st.state=='draft':
                continue
            if st.journal_id.type == 'bank':
                self.write(cr, uid, [st.id], {'state':'draft'}, context=context)
            else:
                done.append(st.id)
        return super(account_bank_statement, self).button_cancel(cr, uid, done, context=context)

    def button_journal_entries(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        ctx = (context or {}).copy()
        ctx['journal_id'] = self.browse(cr, uid, ids[0], context=context).journal_id.id
        move_line_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_move_line_from_bank_form_list')
        act_move_line = {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.move.line',
            'view_id': [move_line_view[1]],
            'type': 'ir.actions.act_window',
            'domain':[('statement_id','in',ids)],
            'context':ctx,
        }
        return act_move_line

    def unpost_statement_moves(self, cr, uid, ids, context):
        move_obj = self.pool.get('account.move')       
        for st in self.browse(cr, uid, ids, context=context):
            if st.state != 'draft':
                raise orm.except_orm(_('Warning !'), _('You are not allowed to Unpost Moves on a Confirmed Bank Statement.'))
            move_ids = list(set([x.move_id.id for x in st.move_line_ids]))       
            posted_move_ids = move_obj.search(cr, uid, [('id', 'in', move_ids), ('state', '=', 'posted')], context=context)
            if posted_move_ids:
                move_obj.button_cancel(cr, uid, posted_move_ids, context=context)
                self.log(cr, uid, st.id, _('Posted Moves of Statement %s have been unposted.') % (st.name))
            else:
                raise orm.except_orm(_('Information !'), _('There are no posted Moves associated with this Bank Statement.'))
        return True

    def post_statement_moves(self, cr, uid, ids, context):
        move_obj = self.pool.get('account.move')       
        for st in self.browse(cr, uid, ids, context=context):
            if st.state=='draft':
                continue
            move_ids = list(set([x.move_id.id for x in st.move_line_ids]))
            draft_move_ids = move_obj.search(cr, uid, [('id', 'in', move_ids), ('state', '=', 'draft')], context=context)
            if draft_move_ids:
                move_obj.button_validate(cr, uid, draft_move_ids, context=context)
                self.log(cr, uid, st.id, _('Draft Moves of Statement %s have been posted.') % (st.name))
        return True

    def unlink(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')
        for st in self.browse(cr, uid, ids, context=context):
            voucher_ids = []
            for st_line in st.line_ids:
                if st_line.voucher_id:
                    if st_line.voucher_id.state == 'posted':
                        raise orm.except_orm(_('Invalid action !'), 
                            _("You cannot delete a bank statement with reconciled payments !   \
                              \nCf. Bank Statement '%s', Transaction Reference '%s'.") %(st.name, st_line.ref))
                    voucher_ids.append(st_line.voucher_id.id)
            voucher_obj.unlink(cr, uid, voucher_ids, context=context)

        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        for st in self.browse(cr, uid, ids, context=context):
            # check posted moves
            move_ids = list(set([x.move_id.id for x in st.move_line_ids]))       
            posted_move_ids = move_obj.search(cr, uid, [('id', 'in', move_ids), ('state', '=', 'posted')], context=context)
            if posted_move_ids:
                raise orm.except_orm(_('Error'),
                    _("You cannot Delete a Bank Statement which has Posted Moves !" \
                      "\nYou can change the state of the Moves via the 'Unpost Moves' button in the 'Journal Entries' tab."))
            # check reconciled entries
            reconcile_ids = []
            for move_line in st.move_line_ids:
                if move_line.reconcile_id or move_line.reconcile_partial_id:
                    reconcile_ids.append(move_line.reconcile_id.id or move_line.reconcile_partial_id.id)                                  
            if reconcile_ids:
                raise orm.except_orm(_('Error'),
                    _("You cannot Delete a Bank Statement which has reconciled Journal Entries !" \
                      "\nYou can undo the reconciliations via the 'Unreconcile Entries' button in the 'Journal Entries' tab."))
            move_obj.unlink(cr, uid, move_ids, context)

        return super(account_bank_statement, self).unlink(cr, uid, ids, context=context)

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        """ 
        Order the Move Lines in a Bank Statement on the Move name in stead of default account.move.line _order 
        """
        if context is None:
            context = {}
        #_logger.warn('read, ids = %s, fields = %s, context = %s', ids, fields, context)
        res = super(account_bank_statement, self).read(cr, uid, ids, fields=fields, context=context, load=load)
        if context.get('journal_type') == 'bank' and len(res) == 1:
            aml_ids = res[0].get('move_line_ids')
            if aml_ids:
                seq_select = "CASE WHEN substring(m.name from '[0-9]*$') = '' THEN 0 ELSE substring(m.name from '[0-9]*$')::INT END AS seq "
                cr.execute('SELECT l.id,' + seq_select + 'FROM account_move_line l ' \
                    'INNER JOIN account_move m on l.move_id=m.id ' \
                    'WHERE l.id in %s ' \
                    'ORDER BY seq, id desc', (tuple(aml_ids),))
                query_result = cr.fetchall()
                aml_ids = [x[0] for x in query_result]
                res[0].update({'move_line_ids': aml_ids})
        return res

