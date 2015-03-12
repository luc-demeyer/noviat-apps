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
from report import report_sxw
import tools
from tools.translate import _
from tools.translate import translate
import logging
_logger = logging.getLogger(__name__)

class nov_journal_fiscalyear_print(report_sxw.rml_parse):
    
    def set_context(self, objects, data, ids, report_type=None):
        #_logger.warn('objects = %s, data = %s, ids = %s', objects, data, ids) 
        cr = self.cr
        uid = self.uid
        context = self.context
        fiscalyear_id = data['fiscalyear_id']
        journal_id = data['journal_id']
        sort = data['sort']
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context)

        self.cr.execute('SELECT account_move_line.move_id as move_id, account_move_line.id as aml_id, ' \
            'account_move.name as move_name, account_move.date as move_date, account_account.code as acc_code, ' \
            'res_partner.name as partner_name, account_move_line.name as aml_name, account_tax_code.code as tax_code, ' \
            'account_move_line.tax_amount as tax_amount, account_move_line.debit, account_move_line.credit, ' \
            'account_invoice.internal_number as inv_number, account_bank_statement.name as st_number, account_voucher.number as voucher_number ' \
            'FROM account_move_line ' \
            'INNER JOIN account_move ON account_move_line.move_id = account_move.id ' \
            'INNER JOIN account_account ON account_move_line.account_id = account_account.id ' \
            'INNER JOIN account_period ON account_move_line.period_id = account_period.id ' \
            'LEFT OUTER JOIN account_invoice ON account_invoice.move_id = account_move.id ' \
            'LEFT OUTER JOIN account_voucher ON account_voucher.move_id = account_move.id ' \
            'LEFT OUTER JOIN account_bank_statement ON account_move_line.statement_id = account_bank_statement.id ' \
            'LEFT OUTER JOIN res_partner ON account_move_line.partner_id = res_partner.id ' \
            'LEFT OUTER JOIN account_tax_code ON account_move_line.tax_code_id = account_tax_code.id  ' \
            'WHERE account_period.fiscalyear_id = %s AND account_move_line.journal_id = %s ' \
            'AND account_move_line.state <> \'draft\' ORDER BY move_id, aml_id' \
            % (fiscalyear_id, journal_id)
        )
        lines = self.cr.dictfetchall()

        # add reference of corresponding legal document
        if journal.type in ['sale', 'sale_refund', 'purchase', 'purchase_refund']:
            map(lambda x: x.update({'docname' : x['inv_number'] or x['voucher_number']}), lines)
        elif journal.type in ['bank', 'cash']:   
            map(lambda x: x.update({'docname' : x['st_number'] or x['voucher_number']}), lines)      
        else:           # journal  type in ['general', 'situation']
            map(lambda x: x.update({'docname' : x['move_name']}), lines)      

        # sort by legal document number or by date
        if sort == 'number' :
            lines.sort(key=lambda x:x['docname'])
        else:
            lines.sort(key=lambda x:x['move_date'])
            lines.sort(key=lambda x:x['docname'])

        # insert a flag in every move_line to indicate the end of a move/statement
        # this flag will be used to draw a full line between moves/statements 
        for cnt in range(len(lines)-1):
            if lines[cnt]['move_name'] <> lines[cnt+1]['move_name']:
                lines[cnt]['draw_line'] = 1
            else:
                lines[cnt]['draw_line'] = 0
        lines[-1]['draw_line'] = 1

        self.localcontext.update( {
            'journal' : journal.name,
            'lines': lines,
        })        
        objects = self.pool.get('account.fiscalyear').browse(self.cr, self.uid, [fiscalyear_id], self.context)
        super(nov_journal_fiscalyear_print, self).set_context(objects, data, [fiscalyear_id])
       
    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(nov_journal_fiscalyear_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,  
        })
        self.context = context
    
    def formatLang(self, value, digits=2, date=False, date_time=False, grouping=True, monetary=False):
        res = super(nov_journal_fiscalyear_print, self).formatLang(value, digits, date, date_time, grouping, monetary)
        if res == '0.00':
            return ''
        else:
            return res  

report_sxw.report_sxw('report.nov.account.journal.fiscalyear.print', 'account.fiscalyear', 'addons/l10n_be_coa_multilang/report/nov_account_journal_fiscalyear.rml', parser=nov_journal_fiscalyear_print,header=False)



