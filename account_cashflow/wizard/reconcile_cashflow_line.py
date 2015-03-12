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
import netsvc
from tools.translate import _


class reconcile_cashflow_line(osv.osv_memory):
    _name = 'reconcile.cashflow.line'
    _description = 'Reconcile selected Cash Flow Lines'

    def _reconcile(self, cr, uid, context=None):        
        if context is None:
            context = {}
        cfline_obj = self.pool.get('account.cashflow.line')
        cfoline_obj = self.pool.get('account.cashflow.line.overview')
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        line_ids = context['active_ids']
        cfpline_ids = filter(lambda x: x<0, line_ids)
        cfline_ids = filter(lambda x: x>0, line_ids)        
        if not cfpline_ids:
            raise osv.except_osv(_('Warning'), _('No Provision Line selected !'))
        elif len(cfpline_ids) > 1:
            raise osv.except_osv(_('Ambiguous selection'), _('Multiple Provision Lines selected !'))
        elif not (cfline_ids):
            raise osv.except_osv(_('Warning'), _('No Cash Flow Lines selected !'))
        else:
            cfpline = cfpline_obj.browse(cr, uid, -cfpline_ids[0])  
            vals = {'cashflow_code_id': cfpline.cfc_normal_id.id}       
            if cfpline.type:
                vals['type'] = cfpline.type
            if cfpline.account_id.id:
                vals['account_id'] = cfpline.account_id.id
        cfline_obj.write(cr, uid, cfline_ids, vals)
        cfpline_obj.write(cr, uid, [cfpline.id], {'state': 'draft'})
        cfpline_obj.unlink(cr, uid, [cfpline.id])
        note = _("\nReconciliation results:")
        note += ("\n\nNumber of lines reconciled: %s") % len(cfline_ids)    
        note += _("\nResulting Cash Flow Code: %s, %s ") % (cfpline.cfc_normal_id.code, cfpline.cfc_normal_id.name)
        return note
    
    _columns = {
        'note': fields.text('Result', readonly=True),
    }
    _defaults = {
        'note': _reconcile,
    }

reconcile_cashflow_line()
