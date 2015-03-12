# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2012 Noviat nv/sa (www.noviat.be). All rights reserved.
# 
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from tools.translate import _
import logging

class account_move(osv.osv):
    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):
        """
        Modify the account_move 'post' behaviour to create link to bank statement after creation 
        of the accounting move lines via the account_voucher 'validate' button
        """
        super(account_move, self).post(cr, uid, ids, context=context)
        #logging.getLogger(self._name).warn('post, ids = %s', ids)
        voucher_obj = self.pool.get('account.voucher')
        move_line_obj = self.pool.get('account.move.line')
        st_line_obj = self.pool.get('account.bank.statement.line')
        st_obj = self.pool.get('account.bank.statement')
        for move in self.browse(cr, uid, ids, context=context):
            voucher_ids = voucher_obj.search(cr, uid, [('move_id', '=', move.id)])
            voucher_id = voucher_ids and voucher_ids[0]
            st_line_ids = st_line_obj.search(cr, uid, [('voucher_id', '=', voucher_id)])
            for st_line_id in st_line_ids:
                st_line = st_line_obj.browse(cr, uid, st_line_id)
                st_line_obj.write(cr, uid, [st_line.id], {'move_ids': [(4, move.id)]})
                move_line_obj.write(cr, uid, [x.id for x in move.line_id], {'statement_id': st_line.statement_id.id}, context=context)
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            for move_line in move.line_id:
                st = move_line.statement_id
                if st and st.state == 'confirm':
                    raise osv.except_osv('Warning', _('Operation not allowed ! \
                        \nYou cannot unpost an Accounting Entry that is linked to a Confirmed Bank Statement.'))
        return super(account_move, self).button_cancel(cr, uid, ids, context=context)

    def button_dummy(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {}, context=context)
    
account_move()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
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
        #logging.getLogger(self._name).warn('fields_view_get, context = %s', context)
        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        if context.get('act_window_from_bank_statement', False) and view_type=='tree':
            model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('module', '=', 'account_bank_statement_voucher'), ('name', '=', 'view_move_line_reconcile_tree')], context=context)
            view_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']        
            context.update({'view_mode':'tree'})
        return super(account_move_line, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)

    def unlink(self, cr, uid, ids, context=None, check=True):
        for move_line in self.browse(cr, uid, ids, context):
            st = move_line.statement_id
            if st and st.state == 'confirm':
                raise osv.except_osv('Warning', _('Operation not allowed ! \
                    \nYou cannot delete an Accounting Entry that is linked to a Confirmed Bank Statement.'))
        return super(account_move_line, self).unlink(cr, uid, ids, context=context, check=check)

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        for move_line in self.browse(cr, uid, ids, context):
            st = move_line.statement_id
            if st and st.state == 'confirm':
                raise osv.except_osv('Warning', _('Operation not allowed ! \
                    \nYou cannot modify an Accounting Entry that is linked to a Confirmed Bank Statement.'))
        return super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check)

account_move_line()