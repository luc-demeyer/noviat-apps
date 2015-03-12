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
from osv import fields, osv
import logging
_logger = logging.getLogger(__name__)

class nov_partner_ledger_fy_close_print(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(nov_partner_ledger_fy_close_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'lines': self.partner_lines,
        })
        self.context = context
    
    def set_context(self, objects, data, ids, report_type=None):
        cr = self.cr
        uid = self.uid
        context = self.context
        fiscalyear_id = data['fiscalyear_id']
        target_move = data['target_move']
        result_selection = data['result_selection']
        company_id = data['company_id']    

        account_obj = self.pool.get('account.account')
        fy_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')

        fiscalyear = fy_obj.browse(cr, uid, fiscalyear_id, context=context)
        fy_code = fiscalyear.code
        title_prefix = _('Fiscal Year %s : ') % fy_code

        # perform query on selected fiscal year as well as periods of preceding fy's.
        fy_date_start = fiscalyear.date_start
        fy_query_ids = fy_obj.search(cr, uid, [('date_stop', '<=', fy_date_start), ('company_id', '=', company_id)])
        fy_query_ids += [fiscalyear_id] 

        receivable_ids = account_obj.search(cr, uid, [('type', '=', 'receivable'), ('company_id', '=', company_id)], order='code')
        for x in account_obj.browse(cr, uid, receivable_ids, context):
            title = title_prefix + _('Open Receivables for account %s ') % x.code
            receivables = [{'a_id': x.id, 'title': title}]
        payable_ids = account_obj.search(cr, uid, [('type', '=', 'payable'), ('company_id', '=', company_id)], order='code')
        for x in account_obj.browse(cr, uid, payable_ids, context):
            title = title_prefix + _('Open Payables for account %s ') % x.code
            payables = [{'a_id': x.id, 'title': title}]
        if result_selection == 'customer':
            account_ids = receivable_ids
            accounts = receivables
        elif result_selection == 'supplier':
            account_ids = payable_ids
            accounts = payables
        else:
            account_ids = receivable_ids + payable_ids
            accounts = receivables + payables

        if target_move == 'posted':
            move_selection = "AND m.state = 'posted' "
            report_info = _('All Posted Entries')
        else:
            move_selection = ''
            report_info = _('All Entries')

        # define subquery to select move_lines within FY that are reconciled after FY
        next_fy_ids = fy_obj.search(cr, uid, [('date_stop', '>', fiscalyear.date_stop), ('company_id', '=', company_id)])
        next_period_ids = period_obj.search (cr, uid, [('fiscalyear_id', 'in', next_fy_ids)]) 
        if next_period_ids:
            subquery = 'OR reconcile_id IN (SELECT reconcile_id FROM account_move_line WHERE period_id IN %s ' \
            'AND reconcile_id IS NOT NULL)' % str(tuple(next_period_ids)).replace(',)', ')')
        else:
            subquery = None

        cr.execute('SELECT l.move_id as m_id, l.id as l_id, l.date as l_date, ' \
            'm.name as move_name, m.date as m_date, a.id as a_id, a.code as a_code, ' \
            'j.id as j_id, j.code as j_code, j.type as j_type, ' \
            'p.id as p_id, p.name as p_name, l.name as l_name, ' \
            'l.debit, l.credit, i.date_due, ' \
            'l.reconcile_id, r.name as r_name, ' \
            'l.reconcile_partial_id, rp.name as rp_name, ' \
            'i.internal_number as inv_number, b.name as st_number, v.number as voucher_number ' \
            'FROM account_move_line l ' \
            'INNER JOIN account_journal j ON l.journal_id = j.id ' \
            'INNER JOIN account_move m ON l.move_id = m.id ' \
            'INNER JOIN account_account a ON l.account_id = a.id ' \
            'INNER JOIN account_period ON l.period_id = account_period.id ' \
            'LEFT OUTER JOIN account_invoice i ON i.move_id = m.id ' \
            'LEFT OUTER JOIN account_voucher v ON v.move_id = m.id ' \
            'LEFT OUTER JOIN account_bank_statement b ON l.statement_id = b.id ' \
            'LEFT OUTER JOIN res_partner p ON l.partner_id = p.id ' \
            'LEFT OUTER JOIN account_move_reconcile r ON l.reconcile_id = r.id ' \
            'LEFT OUTER JOIN account_move_reconcile rp ON l.reconcile_partial_id = rp.id ' \
            'WHERE l.account_id IN %s AND account_period.fiscalyear_id in %s ' + move_selection + \
            'AND (l.reconcile_id IS NULL ' + (subquery or '') + ') '
            'ORDER BY a_code, p_name, p_id, l_date', 
            (tuple(account_ids), tuple(fy_query_ids))
        )
        all_lines = cr.dictfetchall()
        if not all_lines:
            raise osv.except_osv(_('No Data Available'), _('No records found for your selection!'))   

        # add reference of corresponding legal document        
        lines_map = lambda x: (x['j_type'] in ['sale', 'sale_refund', 'purchase', 'purchase_refund'] and (x.update({'docname' : x['inv_number'] or x['voucher_number']}) or True)) \
                        or (x['j_type'] in ['bank', 'cash'] and (x.update({'docname' : x['st_number'] or x['voucher_number']}) or True)) \
                        or (x.update({'docname' : x['move_name']}))                
        map(lines_map, all_lines)

        # insert a flag in every move_line to indicate the end of a partner
        # this flag can be used to draw a full line between partners 
        for cnt in range(len(all_lines)-1):
            if all_lines[cnt]['p_id'] <> all_lines[cnt+1]['p_id']:
                all_lines[cnt]['draw_line'] = 1
            else:
                all_lines[cnt]['draw_line'] = 0
        all_lines[-1]['draw_line'] = 1

        p_map = map(lambda x: {'p_id': x['p_id'], 'p_name': x['p_name']}, all_lines)

        partners = []
        for p in p_map:
            if p['p_id'] not in map(lambda x: x.get('p_id', None), partners):      # remove duplicates while preserving list order
                partners.append(p)                        
                partner_lines = filter(lambda x: x['p_id'] == p['p_id'], all_lines)
                debits = map(lambda x: x['debit'] or 0.0, partner_lines)
                sum_debit = reduce(lambda x,y: x + y, debits)
                credits = map(lambda x: x['credit'] or 0.0, partner_lines)
                sum_credit = reduce(lambda x,y: x + y, credits)
                balance = sum_debit - sum_credit
                p.update({'d': sum_debit, 'c': sum_credit, 'b': balance})

        acc_totals = {}
        for a_id in account_ids:
            sum_debit = 0
            sum_credit = 0
            acc_lines = filter(lambda x: x['a_id'] == a_id, all_lines)
            debits = map(lambda x: x['debit'] or 0.0, acc_lines)
            if debits:
                sum_debit = reduce(lambda x,y: x + y, debits)
            credits = map(lambda x: x['credit'] or 0.0, acc_lines)
            if credits:
                sum_credit = reduce(lambda x,y: x + y, credits)
            balance = sum_debit - sum_credit
            acc_totals.update({a_id: {'d': sum_debit, 'c': sum_credit, 'b': balance}})

        self.localcontext.update( {
            'all_lines': all_lines,
            'report_info': report_info,
            'accounts' : accounts,
            'partners' : partners,
            'acc_totals': acc_totals,    
        })                 

        objects = self.pool.get('account.fiscalyear').browse(self.cr, self.uid, [fiscalyear_id], self.context)
        super(nov_partner_ledger_fy_close_print, self).set_context(objects, data, [fiscalyear_id])

    def partner_lines(self, partner_id):
        return filter(lambda x: x['p_id'] == partner_id, self.localcontext['all_lines'])
    
    def formatLang(self, value, digits=2, date=False, date_time=False, grouping=True, monetary=False):
        res = super(nov_partner_ledger_fy_close_print, self).formatLang(value, digits, date, date_time, grouping, monetary)
        if res == '0.00':
            return ''
        else:
            return res  

report_sxw.report_sxw('report.nov.account.partner.ledger.fy.close.print', 'account.fiscalyear', 'addons/l10n_be_coa_multilang/report/nov_account_partner_ledger_fy_close.rml', parser=nov_partner_ledger_fy_close_print,header=False)
