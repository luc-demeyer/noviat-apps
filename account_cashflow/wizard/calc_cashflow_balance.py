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

class calc_cashflow_balance(osv.osv_memory):
    _name = 'calc.cashflow.balance'
    _description = 'Recalculate Cash Flow Balances'
    _columns = {
        'date_start': fields.date('Start Date', required=True),
        'date_stop': fields.date('End Date', required=True),
        'journal_ids': fields.many2many('account.journal', string='Financial Journal(s)', domain=[('type', '=', 'bank')], required=True),  
    }
    
    _defaults = {
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),
        'date_stop': lambda *a: time.strftime('%Y-%m-%d'),
    }
    
    def calc_cashflow_balance(self, cr, uid, ids, context=None):
        cfbalance_obj = self.pool.get('account.cashflow.balance')
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

        for journal_id in journal_ids:
            for x in range(0, nbr_days):
                day = (date_start + timedelta(days=x)).isoformat()
                # calculate balances
                cr.execute('SELECT cashflow_code_id, sum(amount) FROM ( ' \
                    '(SELECT c.cashflow_code_id AS cashflow_code_id, sum(l.amount) AS amount ' \
                        'FROM account_cashflow_line AS c '\
                        'INNER JOIN account_bank_statement_line AS l ON c.st_line_id=l.id ' \
                        'WHERE l.val_date = %s AND c.cashflow_code_id IS NOT NULL AND l.journal_id = %s ' \
                        'GROUP BY c.cashflow_code_id) ' \
                    'UNION ' \
                    '(SELECT p.cashflow_code_id AS cashflow_code_id, sum(p.amount) AS amount ' \
                        'FROM account_cashflow_provision_line AS p ' \
                        'WHERE p.val_date = %s AND p.journal_id = %s ' \
                        'GROUP BY p.cashflow_code_id) ' \
                    ') AS u GROUP BY u.cashflow_code_id', 
                    (day, journal_id, day, journal_id))
                balances = cr.fetchall()
                # delete old balances
                bal_ids = cfbalance_obj.search(cr, uid, [('date', '=', day), ('journal_id', '=', journal_id)])
                if bal_ids:
                    cfbalance_obj.unlink(cr, uid, bal_ids)
                # create new balances with the calculated values
                for balance in balances:
                    cfbalance_obj.create(cr, uid, {
                        'date': day,
                        'cashflow_code_id': balance[0],
                        'balance': balance[1],  
                        'journal_id': journal_id,
                        })
        return {}

calc_cashflow_balance()


