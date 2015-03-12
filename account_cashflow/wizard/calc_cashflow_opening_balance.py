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
from datetime import datetime, date, timedelta
from osv import osv, fields
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class calc_cashflow_opening_balance(osv.osv_memory):
    _name = 'calc.cashflow.opening.balance'
    _description = 'Recalculate Cash Flow Opening Balances'
    _columns = {
        'date_start': fields.date('Start Date', required=True),
        'date_stop': fields.date('End Date', required=True),
        'journal_ids': fields.many2many('account.journal', string='Financial Journal(s)', domain=[('type', '=', 'bank')], required=True),  
    }
    _defaults = {
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),
        'date_stop': lambda *a: time.strftime('%Y-%m-%d'),
    }
    
    def calc_cashflow_opening_balance(self, cr, uid, ids, context=None):
        balopen_obj = self.pool.get('account.cashflow.opening.balance')
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, [], context=context)[0]
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
        date_stop = datetime.strptime(data['date_stop'], '%Y-%m-%d').date()
        journal_ids = data['journal_ids']
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id,
        nbr_days = (date_stop - date_start).days + 1
        if nbr_days < 1 :
            raise osv.except_osv(_('Error!'), _('Invalid Date Range!'))
            return {}

        cr.execute("SELECT id FROM account_cashflow_code WHERE type='init' AND company_id = %s", (company_id,))
        res_init_id = cr.fetchall()
        if len(res_init_id) != 1:
            err_str = len(res_init_id) and 'Multiple' or 'No' 
            raise osv.except_osv('Configuration Error', 
                _("%s Cash Flow Codes of type='Initial Balance' defined for your Company !") % err_str)
        balance_init_id = res_init_id[0][0]

        for x in range(0, nbr_days):
            date = (date_start + timedelta(days=x)).isoformat()
            balopen_obj.calc_opening_balance(cr, uid, date, balance_init_id, journal_ids)

        return {}

calc_cashflow_opening_balance()


