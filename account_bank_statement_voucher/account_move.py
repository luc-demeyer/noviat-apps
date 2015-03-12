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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import pickle
import logging
_logger = logging.getLogger(__name__)


class account_move(orm.Model):
    _inherit = 'account.move'

    def _reopen(self, context):
        act_move = pickle.loads(str(context['wizard_action']))
        act_move['context'] = context
        return act_move

    def absv_button_validate(self, cr, uid, ids, context=None):
        super(account_move, self).button_validate(cr, uid, ids, context=context)
        return self._reopen(context)

    def absv_button_cancel(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            for move_line in move.line_id:
                st = move_line.statement_id
                if st and st.state == 'confirm':
                    raise orm.except_orm('Warning', _('Operation not allowed ! \
                        \nYou cannot unpost an Accounting Entry that is linked to a Confirmed Bank Statement.'))
        super(account_move, self).button_cancel(cr, uid, ids, context=context)
        return self._reopen(context)

    def absv_button_save(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {}, context=context)
        return self._reopen(context)

    def absv_button_save_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {}, context=context)
        return True


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    _columns = {
        'move_state': fields.related('move_id', 'state', type='char', relation='account.move',
            string='Move State', readonly=True),
    }

    def onchange_tax_code(self, cr, uid, ids, tax_code_id, debit, credit):
        val = {}
        if tax_code_id:
            if debit or credit:
                val['tax_amount'] = debit or credit
            else:
                 move_lines = self.browse(cr, uid, ids)
                 for move_line in move_lines:
                     if move_line.debit or move_line.credit:
                        val['tax_amount'] = move_line.debit or move_line.credit
        else:
            val['tax_amount'] = False
        return {'value': val}

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        #_logger.warn('fields_view_get, context = %s, view_type= %s', context, view_type)
        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        if context.get('act_window_from_bank_statement', False):
            if view_type=='tree':
                model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('module', '=', 'account_bank_statement_voucher'), ('name', '=', 'view_move_line_reconcile_tree')], context=context)
                view_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']        
                context.update({'view_mode':'tree'})
            elif view_type=='search':
                model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('module', '=', 'account_bank_statement_voucher'), ('name', '=', 'view_move_line_reconcile_search')], context=context)
                view_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']        
                context.update({'view_mode':'search'})
        return super(account_move_line, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        #_logger.warn('%s, search, args=%s, context=%s', self._name, args, context)
        if context is None: context = {}
        if context.get('act_window_from_bank_statement'):
            in_ids = context.get('entries')
            # refine query with invoice number matching
            pos = 0
            while pos < len(args):
                if args[pos][0] == 'invoice' and args[pos][1] in ('like', 'ilike') and args[pos][2]:
                    if in_ids:
                        query2 = "AND aml.id IN (%s)" % ','.join(['%s'] * len(in_ids)) %tuple(in_ids)
                    else:
                        query2 = "AND company_id=%s" %context['company_id']
                    query = "SELECT aml.id " \
                       "FROM account_move_line aml " \
                       "INNER JOIN account_invoice ai ON aml.move_id = ai.move_id " \
                       "WHERE ai.number ILIKE '%" + args[pos][2] + "%'"
                    cr.execute(query + query2)
                    res = cr.fetchall()
                    out_ids = [x[0] for x in res]
                    args[pos] = ('id', 'in', out_ids)
                pos += 1
        #_logger.warn('%s, search, exit args=%s', self._name, args)
        return super(account_move_line, self).search(cr, uid, args, offset, limit, order, context, count)

    def unlink(self, cr, uid, ids, context=None, check=True):
        for move_line in self.browse(cr, uid, ids, context):
            st = move_line.statement_id
            if st and st.state == 'confirm':
                raise orm.except_orm('Warning', _('Operation not allowed ! \
                    \nYou cannot delete an Accounting Entry that is linked to a Confirmed Bank Statement.'))
        return super(account_move_line, self).unlink(cr, uid, ids, context=context, check=check)

    def create(self, cr, uid, vals, context=None, check=True):
        #_logger.warn('%s, create, vals=%s, context=%s', self._name, vals, context)
        if not context: context = {}
        if context.get('act_window_from_bank_statement'):
            if not vals.get('statement_id'):
                vals['statement_id'] = context['statement_id']
        return super(account_move_line, self).create(cr, uid, vals, context, check)

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        #_logger.warn('write, vals = %s', vals)
        for move_line in self.browse(cr, uid, ids, context):
            st = move_line.statement_id
            if st and st.state == 'confirm':
                if vals.keys() not in [['reconcile_id'],['reconcile_partial_id']]:
                    raise orm.except_orm('Warning', _('Operation not allowed ! \
                        \nYou cannot modify an Accounting Entry that is linked to a Confirmed Bank Statement. \
                        \nStatement = %s\nMove = %s (id:%s)\nUpdate Values = %s') 
                        %(st.name, move_line.move_id.name, move_line.move_id.id, vals))
        return super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check)
