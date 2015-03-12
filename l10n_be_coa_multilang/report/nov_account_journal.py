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
import netsvc
logger=netsvc.Logger()
#
# Use period and Journal for selection or resources
#
class nov_journal_print(report_sxw.rml_parse):
    
    def set_context(self, objects, data, ids, report_type=None):
        #logger.notifyChannel('addons.'+__name__, netsvc.LOG_WARNING, 'set_context, objects = %s, data = %s, ids = %s' % (objects, data, ids)) 
        cr = self.cr
        uid = self.uid
        context = self.context
        journal_ids = data['journal_ids']
        period_ids = data['period_ids']
        sort = data['sort']     
        self.localcontext.update( {
            'journals' : self.pool.get('account.journal').browse(cr, uid, journal_ids, context),
            'periods': self.pool.get('account.period').browse(cr, uid, period_ids, context),
        })
        cr.execute('SELECT id FROM ' \
            '(SELECT id, name, journal_id, period_id FROM account_journal_period WHERE journal_id IN %s) AS sq ' \
            'WHERE period_id IN %s ORDER BY name',
            (tuple(journal_ids), tuple(period_ids))
        )       
        new_ids = map(lambda x: x[0], cr.fetchall())
        objects = self.pool.get('account.journal.period').browse(cr, uid, new_ids, context)
        super(nov_journal_print, self).set_context(objects, data, new_ids)
       
    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(nov_journal_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'lines': self.lines,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'tax_codes': self.tax_codes,
            'sum_vat': self._sum_vat,            
        })
        self.context = context
    
    def lines(self, period, journal, sort, *args):
        period_id = period.id
        journal_id = journal.id
        # update status period
        ids_journal_period = self.pool.get('account.journal.period').search(self.cr, self.uid, 
            [('journal_id', '=', journal_id), ('period_id', '=', period_id)])      
        if ids_journal_period:
            self.cr.execute(
                'update account_journal_period set state=%s where journal_id=%s and period_id=%s and state=%s', 
                ('printed', journal_id, period_id, 'draft')
            )
            self.cr.commit()        

        self.cr.execute('SELECT account_move_line.move_id as move_id, account_move_line.id as aml_id, ' \
            'account_move.name as move_name, account_move.date as move_date, account_account.code as acc_code, ' \
            'res_partner.name as partner_name, account_move_line.name as aml_name, account_tax_code.code as tax_code, ' \
            'account_move_line.tax_amount as tax_amount, account_move_line.debit, account_move_line.credit, ' \
            'account_invoice.internal_number as inv_number, account_bank_statement.name as st_number, account_voucher.number as voucher_number ' \
            'FROM account_move_line ' \
            'INNER JOIN account_move ON account_move_line.move_id = account_move.id ' \
            'INNER JOIN account_account ON account_move_line.account_id = account_account.id ' \
            'LEFT OUTER JOIN account_invoice ON account_invoice.move_id = account_move.id ' \
            'LEFT OUTER JOIN account_voucher ON account_voucher.move_id = account_move.id ' \
            'LEFT OUTER JOIN account_bank_statement ON account_move_line.statement_id = account_bank_statement.id ' \
            'LEFT OUTER JOIN res_partner ON account_move_line.partner_id = res_partner.id ' \
            'LEFT OUTER JOIN account_tax_code ON account_move_line.tax_code_id = account_tax_code.id  ' \
            'WHERE account_move_line.period_id = %s AND account_move_line.journal_id = %s ' \
            'AND account_move_line.state <> \'draft\' ORDER BY move_id, aml_id' \
            % (period_id, journal_id)
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
        return lines

    def tax_codes(self, period, journal):
        period_id = period.id
        journal_id = journal.id
        ids_journal_period = self.pool.get('account.journal.period').search(self.cr, self.uid, 
            [('journal_id', '=', journal_id), ('period_id', '=', period_id)])      
        self.cr.execute(
            'select distinct tax_code_id from account_move_line ' \
            'where period_id=%s and journal_id=%s and tax_code_id is not null and state<>\'draft\'',
            (period_id, journal_id)
        )
        ids = map(lambda x: x[0], self.cr.fetchall())
        tax_code_ids = []
        if ids:
            self.cr.execute('select id from account_tax_code where id in %s order by code', (tuple(ids),))        
            tax_code_ids = map(lambda x: x[0], self.cr.fetchall())
        tax_codes = self.pool.get('account.tax.code').browse(self.cr, self.uid, tax_code_ids, self.context)
        return tax_codes

    def _sum_debit(self, period_id, journal_id):
        self.cr.execute('select sum(debit) from account_move_line where period_id=%s and journal_id=%s and state<>\'draft\'', (period_id, journal_id))
        return self.cr.fetchone()[0] or 0.0

    def _sum_credit(self, period_id, journal_id):
        self.cr.execute('select sum(credit) from account_move_line where period_id=%s and journal_id=%s and state<>\'draft\'', (period_id, journal_id))
        return self.cr.fetchone()[0] or 0.0

    def _sum_vat(self, period_id, journal_id, tax_code_id):
        self.cr.execute('select sum(tax_amount) from account_move_line where ' \
                        'period_id=%s and journal_id=%s and tax_code_id=%s and state<>\'draft\'',
                        (period_id, journal_id, tax_code_id))
        return self.cr.fetchone()[0] or 0.0
    
    def formatLang(self, value, digits=2, date=False,date_time=False, grouping=True, monetary=False):
        res = super(nov_journal_print, self).formatLang(value, digits, date, date_time, grouping, monetary)
        if res == '0.00':
            return ''
        else:
            return res  

report_sxw.report_sxw('report.nov.account.journal.period.print', 'account.journal.period', 'addons/l10n_be_coa_multilang/report/nov_account_journal.rml', parser=nov_journal_print,header=False)



