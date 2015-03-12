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

import time
from osv import osv, fields
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class assign_cashflow_code(osv.osv_memory):
    _name = 'assign.cashflow.code'
    _description = 'Assign Cash Flow Code to selected Cash Flow Lines'

    def warning(self, cr, uid, ids, context):       
        line_ids = context['active_ids']
        note = _('\nAre you sure ?')
        note += _('\n\nNumber of lines selected : %s') % len(line_ids)

        line_obj = self.pool.get('account.cashflow.line')
        draft_ids = line_obj.search(cr, uid, [('id', 'in', line_ids), ('state', '=', 'draft')], context=context) 
        if len(line_ids) <> len(draft_ids):
            note += _("\nOnly lines in 'Draft' state will be updated!")
            note += _("\nNumber of 'Draft' lines selected : %s") % len(draft_ids)
            context.update({'active_ids': draft_ids})
        vals = {
            'state': 'ok',
            'note': note
        }
        self.write(cr, uid, ids, vals, context=context)
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_assign_cashflow_code')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': _('Assign Cash Flow Code done'),
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'assign.cashflow.code',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
        }
        
    def update_lines(self, cr, uid, ids, context):       
        line_ids = context['active_ids']
        cashflow_code_id = self.read(cr, uid, ids, ['cashflow_code_id'], context=context)[0]['cashflow_code_id'][0]
        line_obj = self.pool.get('account.cashflow.line')
        line_obj.write(cr, uid, line_ids, {'cashflow_code_id': cashflow_code_id}, context=context)
        vals = {
            'state': 'done',
            'note': _('\nNumber of updates : %s') % len(line_ids)
        }
        self.write(cr, uid, ids, vals, context=context)
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_assign_cashflow_code')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': _('Assign Cash Flow Code done'),
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'assign.cashflow.code',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
        } 
    
    _columns = {
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', 
            domain=[('type', '=', 'normal')], required=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('ok', 'Ok'),            
            ('done', 'Done')], 
            'State', required=True, readonly=True),        
        'note':fields.text('Result', readonly=True),
    }
    _defaults = {
        'state': 'draft',
    }

assign_cashflow_code()


class assign_cashflow_code_all_line(osv.osv_memory):
    _name = 'assign.cashflow.code.all.line'
    _description = 'Assign Cash Flow Code to selected Cash Flow Lines'

    def warning(self, cr, uid, ids, context):       
        line_ids = context['active_ids']
        note = _('\nAre you sure ?')
        note += _('\n\nNumber of lines selected : %s') % len(line_ids)
        oline_obj = self.pool.get('account.cashflow.line.overview')
        draft_ids = oline_obj.search(cr, uid, [('id', 'in', line_ids), ('state', '=', 'draft')], context=context) 
        if len(line_ids) <> len(draft_ids):
            note += _("\nOnly lines in 'Draft' state will be updated!")
            note += _("\nNumber of 'Draft' lines selected : %s") % len(draft_ids)
            context.update({'active_ids': draft_ids})
        vals = {
            'state': 'ok',
            'note': note
        }
        self.write(cr, uid, ids, vals, context=context)
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_assign_cashflow_code_all_line')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': _('Assign Cash Flow Code done'),
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'assign.cashflow.code.all.line',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
        }
        
    def update_lines(self, cr, uid, ids, context):       
        line_ids = context['active_ids']
        cfc = self.browse(cr, uid, ids[0]).cashflow_code_id
        cline_obj = self.pool.get('account.cashflow.line')
        pline_obj = self.pool.get('account.cashflow.provision.line')
        cline_ids = []
        pline_ids = []
        for i in line_ids:
            if i < 0:
                pline_ids += [-i]
            else:
                cline_ids += [i]       
        cline_obj.write(cr, uid, cline_ids, {'cashflow_code_id': cfc.id}, context=context)
        pline_obj.write(cr, uid, pline_ids, {'cashflow_code_id': cfc.twin_id.id}, context=context)
        vals = {
            'state': 'done',
            'note': _('\nNumber of updates : %s') % len(line_ids)
        }
        self.write(cr, uid, ids, vals, context=context)
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_assign_cashflow_code_all_line')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': _('Assign Cash Flow Code done'),
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'assign.cashflow.code.all.line',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
        } 
    
    _columns = {
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', 
            context={'search_origin': _name},
            domain=[('type', '=', 'normal')], required=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('ok', 'Ok'),            
            ('done', 'Done')], 
            'State', required=True, readonly=True),        
        'note':fields.text('Result', readonly=True),
    }
    _defaults = {
        'state': 'draft',
    }

assign_cashflow_code_all_line()
