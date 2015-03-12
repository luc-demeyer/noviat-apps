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
from math import ceil
from report import report_sxw
from osv import osv
from tools.translate import _
import netsvc
logger=netsvc.Logger()

class account_cashflow_report(report_sxw.rml_parse):
           
    def __init__(self, cr, uid, name, context):
        super(account_cashflow_report, self).__init__(cr, uid, name, context=context)
        #logger.notifyChannel('addons.'+__name__, netsvc.LOG_WARNING, '_init, name = %s, context = %s' % (name, context)) 
        self.context = context
        cr = self.cr
        uid = self.uid

        if not context.get('date_start', None):
            raise osv.except_osv(_('Warning!'), _('This report is only available from the Cash Flow Chart!'))
            return {}

        format_date = self.pool.get('account.cashflow.code').format_date
        date_start = datetime.strptime(context.get('date_start'), '%Y-%m-%d').date()            
        nbr_days = int(context.get('nbr_days'))
        days = [date_start.isoformat()] + [(date_start + timedelta(days=x)).isoformat() for x in range(1, nbr_days)]        

        self.localcontext.update({
            'time': time,
            'timedelta': timedelta,
            'ceil': ceil,
            'cr': cr,
            'uid': uid,
            'name_get': self._name_get,
            'lang': context.get('lang', 'en_US'),
            'date_start': days[0],
            'date_stop': days[-1],
            'nbr_days': nbr_days,
            'days': days,
            'balance_period': self._balance_period,            
        })

    def set_context(self, objects, data, ids, report_type=None):
        cr = self.cr
        uid = self.uid
        context = self.context
        cfc_obj = self.pool.get('account.cashflow.code')
        active_cfc = objects[0]
        
        def _get_toplevel_cfc(record):
            toplevel_cfc = record
            parent = record.parent_id
            if parent:
                toplevel_cfc = _get_toplevel_cfc(parent)
            return toplevel_cfc
        toplevel_cfc = _get_toplevel_cfc(active_cfc)       
        cfc_tree_ids = cfc_obj.search(cr, uid, [('parent_id', 'child_of', [toplevel_cfc.id])], context=context)
        cfc_tree = cfc_obj.browse(cr, uid, cfc_tree_ids, context=context)
        
        cfc_level = 0
        cfc_levels = {toplevel_cfc.id:0}
        for cfc in cfc_tree[1:]:
            if cfc.parent_id.id in cfc_levels:
                cfc_level = cfc_levels[cfc.parent_id.id] + 1
            else:
                cfc_level += 1                
            cfc_levels[cfc.id] = cfc_level
        data['cfc_levels'] = cfc_levels
        super(account_cashflow_report, self).set_context(cfc_tree, data, cfc_tree_ids, report_type=report_type)
            
    def _name_get(self, object):
        res = self.pool.get(object._name).name_get(self.cr, self.uid, [object.id], self.context)
        return res[0][1]

    def _balance_period(self, ids, date_start=None, date_stop=None, day=None):
        res = self.pool.get('account.cashflow.code')._balance_period(self.cr, self.uid, ids, context=self.context, date_start=date_start, date_stop=date_stop, day=day)
        balance = res.values()[0]
        return balance

report_sxw.report_sxw('report.account.cashflow.report',
                       'account.cashflow.code', 
                       'account_cashflow/report/account_cashflow_report.mako',
                       parser=account_cashflow_report)

report_sxw.report_sxw('report.account.cashflow.summary.report',
                       'account.cashflow.code', 
                       'account_cashflow/report/account_cashflow_summary_report.mako',
                       parser=account_cashflow_report)
