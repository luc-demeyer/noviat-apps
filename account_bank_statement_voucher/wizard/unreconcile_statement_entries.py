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
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)


class unreconcile_statement_entries(orm.TransientModel):
    _name = 'unreconcile.statement.entries'
    _description = 'Unreconcile Bank Statement Accounting Entries'

    def _get_defaults(self, cr, uid, context, result='None'):
        st_obj = self.pool.get('account.bank.statement')
        move_line_obj = self.pool.get('account.move.line')
        move_obj = self.pool.get('account.move')
        inv_obj = self.pool.get('account.invoice')
        voucher_ids = []
        reconcile_ids = []
        move_ids = []
        inv_ids = []
        note = ''

        if len(context.get('active_ids', [])) <> 1:        
            return True
        else:
            st = st_obj.browse(cr, uid, context['active_id'], context=context)
            
        for st_line in st.line_ids:
            if st_line.voucher_id:
                voucher_ids.append(st_line.voucher_id.id)
                
        for move_line in st.move_line_ids:
            if move_line.reconcile_id or move_line.reconcile_partial_id:
                reconcile_ids.append(move_line.reconcile_id.id or move_line.reconcile_partial_id.id)                                  
                
        if reconcile_ids:
            moves_note = '\n\nAssociated Moves:\n'      
            move_line_ids = move_line_obj.search(cr, uid, ['|',
                ('reconcile_id', 'in', reconcile_ids),
                ('reconcile_partial_id', 'in', reconcile_ids)
                ])
            for id in move_line_ids: 
                move_ids.append(move_line_obj.browse(cr, uid, id).move_id.id)
            move_ids = list(set(move_ids))
            move_names = move_obj.name_get(cr, uid, move_ids, context=context)
            moves_note += ', '.join(map(lambda x: x[1], move_names))
            inv_ids = inv_obj.search(cr, uid, [('move_id', 'in', move_ids)])
            if inv_ids:
                note += 'Associated Invoices:\n'
                inv_names = inv_obj.name_get(cr, uid, inv_ids, context=context)
                note += ', '.join(map(lambda x: x[1], inv_names))
            note += moves_note
            
        if voucher_ids:
            voucher_note = '\n\nAssociated Payment Vouchers:\n'    
            voucher_note += ', '.join([str(x) for x in voucher_ids])
            note += voucher_note

        if not (reconcile_ids or voucher_ids):
            raise orm.except_orm(_('Information !'), _('There are no reconciled Entries in this Bank Statement.'))
        else:
            if result=='reconcile_ids':
                return reconcile_ids
            elif result=='move_ids':
                return move_ids
            elif result=='voucher_ids':
                return voucher_ids
            elif result=='inv_ids':
                return inv_ids            
            elif result=='note':
                return note
            else:
                raise orm.except_orm(_('Error !'), _('Programming Error.'))

    _columns = {
        'state': fields.selection([
            ('draft', 'Reconciled'),
            ('done', 'Unreconciled')], 
            'State', required=True, readonly=True),
        'reconcile_ids': fields.many2many('account.move.reconcile', 'account_move_reconcile_rel_', 'wiz_id', 'rec_id', 'Reconcile IDs', readonly=True),
        'inv_ids': fields.many2many('account.invoice', 'account_invoice_rel_', 'wiz_id', 'inv_id', 'Associated Invoices', readonly=True),
        'move_ids': fields.many2many('account.move', 'account_move_rel_', 'wiz_id', 'move_id', 'Associated Moves', readonly=True),
        'voucher_ids': fields.many2many('account.voucher', 'account_voucher_rel_', 'wiz_id', 'voucher_id', 'Associated Vouchers', readonly=True),        
        'note':fields.text('Notes', readonly=True),
    }
    _defaults = {
        'state': 'draft',
        'reconcile_ids': lambda self, cr, uid, context : self._get_defaults(cr, uid, context, result='reconcile_ids'),
        'inv_ids': lambda self, cr, uid, context : self._get_defaults(cr, uid, context, result='inv_ids'),
        'move_ids': lambda self, cr, uid, context : self._get_defaults(cr, uid, context, result='move_ids'),
        'voucher_ids': lambda self, cr, uid, context : self._get_defaults(cr, uid, context, result='voucher_ids'),        
        'note': lambda self, cr, uid, context : self._get_defaults(cr, uid, context, result='note'),
    }

    def unreconcile(self, cr, uid, ids, context):
        reconcile_ids = self.read(cr, uid, ids, ['reconcile_ids'], context=context)[0]['reconcile_ids']
        self.pool.get('account.move.reconcile').unlink(cr, uid, reconcile_ids)

        inv_ids = self.read(cr, uid, ids, ['inv_ids'], context=context)[0]['inv_ids']
        for inv_id in inv_ids:
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'open_test', cr)      

        voucher_ids = self.read(cr, uid, ids, ['voucher_ids'], context=context)[0]['voucher_ids'] 
        self.pool.get('account.voucher').cancel_voucher(cr, uid, voucher_ids, context=context)

        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def view_invoices(self, cr, uid, ids, context):
        inv_ids = self.read(cr, uid, ids, ['inv_ids'], context=context)[0]['inv_ids']
        return {
            'domain': "[('id','in', %s)]" % str(inv_ids), 
            'name': _('View Associated Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            }

    def view_moves(self, cr, uid, ids, context):
        move_ids = self.read(cr, uid, ids, ['move_ids'], context=context)[0]['move_ids']
        return {
            'domain': "[('id','in', %s)]" % str(move_ids), 
            'name': _('View Associated Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            }
