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

from osv import fields,osv
import time
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class bank_statement_balance_print(osv.osv_memory):
    _name = 'bank.statement.balance.print'
    _description = 'Bank Statement Balances Report'
    _columns = {
        'date_balance': fields.date('Date', required=True),
        'journal_ids': fields.many2many('account.journal', 'account_journal_rel', 'bsbp_id', 'journal_id', 'Financial Journal(s)', 
            domain=[('type', '=', 'bank')],  
            help = 'Select here the Financial Journal(s) you want to include in your Bank Statement Balances Report.'),
 
    }
    _defaults = {
        'date_balance': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def balance_print(self, cr, uid, ids, context=None):
        #_logger.warn('statement_print, ids = %s, context = %s' % (ids, context))
        if context is None:
            context = {}          
        try:            
            data = self.read(cr, uid, ids, [], context=context)[0]
        except:
            raise osv.except_osv(_('Error!'), _('Wizard in incorrect state. Please hit the Cancel button!'))
            return {}
        datas = {
            'ids': [],
            'model': 'account.bank.statement',
            'date_balance': data['date_balance'],
            'journal_ids': data['journal_ids'], 
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bank.statement.balance.report',
            'datas': datas,
        }        
        
bank_statement_balance_print()
