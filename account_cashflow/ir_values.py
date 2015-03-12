# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2011 Noviat nv/sa (www.noviat.be). All rights reserved.
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
from datetime import datetime, date, timedelta
from osv import osv,fields
from tools.translate import _
import netsvc
logger=netsvc.Logger()

class ir_values(osv.osv):
    _inherit = 'ir.values'

    def get(self, cr, uid, key, key2, models, meta=False, context={}, res_id_req=False, without_user=True, key2_req=True):
#        logger.notifyChannel('addons.'+__name__, netsvc.LOG_WARNING, 'get, context = %s' % (context)) 
        res = super(ir_values, self).get(cr, uid, key, key2, models, meta=False, context=context, res_id_req=False, without_user=True, key2_req=True)

        if models[0][0] == 'account.cashflow.code' and key2 == 'tree_but_open':
            val_tuple = res[0]

            module, xml_id = 'account_cashflow', 'ir_open_cashflow_line'
            res_model, res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
            if val_tuple[0] != res_id:
                return res

            cfc_id = models[0][1]
            if cfc_id == context.get('balance_init_id'):
                return []
            
            cfc_obj = self.pool.get('account.cashflow.code')
            format_date = cfc_obj.format_date
            action = val_tuple[2].copy()
            ctx = eval(action.get('context') or '{}') 
            
            title = cfc_obj.browse(cr, uid, cfc_id).code
            active_column = context.get('tree_but_open_column')
            if active_column and active_column[:11] == 'balance_day': 
                date_start = datetime.strptime(context.get('date_start'), '%Y-%m-%d').date()    
                d = int(active_column[11:13])-1
                day = date_start + timedelta(days=d)
                day_ui = format_date(cr, uid, day, context)
                ctx.update({'active_day': day.isoformat()})
                title += ': ' + day_ui
            else:
                if context.get('date_start'):
                    date_start_ui = format_date(cr, uid, datetime.strptime(context['date_start'], '%Y-%m-%d').date(), context) 
                    date_stop_ui = format_date(cr, uid, datetime.strptime(context['date_stop'], '%Y-%m-%d').date(), context)                    
                    title +=  ': ' + date_start_ui + '..' + date_stop_ui
            action.update({'name': title})           
            ctx.update({'tree_but_open_column': active_column})
            action.update({'context': str(ctx)})
            return [(val_tuple[0], val_tuple[1], action)]

        else:
            return res

ir_values()
