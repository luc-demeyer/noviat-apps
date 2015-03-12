# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-now Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import orm
import logging
_logger = logging.getLogger(__name__)


class partner_open_arap_print(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(partner_open_arap_print, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        cr = self.cr
        uid = self.uid
        context = self.context

        fy_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')

        posted = (data['target_move'] == 'posted') and True or False
        result_selection = data['result_selection']
        company_id = data['company_id']

        by_fy = False
        if data.get('fiscalyear_id'):
            by_fy = True
            fiscalyear_id = data['fiscalyear_id']
            fiscalyear = fy_obj.browse(
                cr, uid, fiscalyear_id, context=context)
            fy_code = fiscalyear.code
            title_prefix = _('Fiscal Year') + ' %s : ' % fy_code
            title_short_prefix = fy_code

            # perform query on selected fiscal year as well as
            # periods of preceding fy's.
            fy_date_start = fiscalyear.date_start
            fy_query_ids = fy_obj.search(
                cr, uid,
                [('date_stop', '<=', fy_date_start),
                 ('company_id', '=', company_id)])
            fy_query_ids += [fiscalyear_id]
            # find periods to select move_lines within
            # FY that are reconciled after FY
            next_fy_ids = fy_obj.search(
                cr, uid,
                [('date_stop', '>', fiscalyear.date_stop),
                 ('company_id', '=', company_id)])
            next_period_ids = period_obj.search(
                cr, uid, [('fiscalyear_id', 'in', next_fy_ids)])

        if data.get('period_id'):
            period_id = data['period_id']
            period = period_obj.browse(cr, uid, period_id, context=context)
            period_code = period.code
            title_prefix = _('Period') + ' %s : ' % period_code
            title_short_prefix = period_code

            # perform query on selected period as well as preceding periods.
            period_date_start = period.date_start
            period_query_ids = period_obj.search(
                cr, uid,
                [('date_stop', '<=', period_date_start),
                 ('company_id', '=', company_id)])
            period_query_ids += [period_id]
            # find periods to select move_lines
            # that are reconciled after period
            next_period_ids = period_obj.search(
                cr, uid,
                [('date_stop', '>', period.date_stop),
                 ('company_id', '=', company_id)])

        report_ar = {
            'type': 'receivable',
            'title': title_prefix + _('Open Receivables'),
            'title_short': title_short_prefix + ', ' + _('AR')}
        report_ap = {
            'type': 'payable',
            'title': title_prefix + _('Open Payables'),
            'title_short': title_short_prefix + ', ' + _('AP')}

        query_start = "SELECT l.move_id as m_id, l.id as l_id, " \
            "l.date as l_date, " \
            "m.name as move_name, m.date as m_date, " \
            "a.id as a_id, a.code as a_code, a.type as a_type, " \
            "j.id as j_id, j.code as j_code, j.type as j_type, " \
            "p.id as p_id, p.name as p_name, p.ref as p_ref, " \
            "l.name as l_name, " \
            "l.debit, l.credit, ai.date_due, " \
            "l.reconcile_id, r.name as r_name, " \
            "l.reconcile_partial_id, rp.name as rp_name, " \
            "ai.internal_number as inv_number, b.name as st_number, " \
            "v.number as voucher_number " \
            "FROM account_move_line l " \
            "INNER JOIN account_journal j ON l.journal_id = j.id " \
            "INNER JOIN account_move m ON l.move_id = m.id " \
            "INNER JOIN account_account a ON l.account_id = a.id " \
            "INNER JOIN account_period ON l.period_id = account_period.id " \
            "LEFT OUTER JOIN account_invoice ai ON ai.move_id = m.id " \
            "LEFT OUTER JOIN account_voucher v ON v.move_id = m.id " \
            "LEFT OUTER JOIN account_bank_statement b " \
            "ON l.statement_id = b.id " \
            "LEFT OUTER JOIN res_partner p ON l.partner_id = p.id " \
            "LEFT OUTER JOIN account_move_reconcile r " \
            "ON l.reconcile_id = r.id " \
            "LEFT OUTER JOIN account_move_reconcile rp " \
            "ON l.reconcile_partial_id = rp.id "

        if posted:
            move_selection = "AND m.state = 'posted' "
            report_info = _('All Posted Entries')
        else:
            move_selection = ''
            report_info = _('All Entries')

        if by_fy:
            move_selection += "AND account_period.fiscalyear_id in %s " % str(
                tuple(fy_query_ids)).replace(',)', ')')
        else:
            move_selection += "AND account_period.id in %s" % str(
                tuple(period_query_ids)).replace(',)', ')')

        # define subquery to select move_lines within FY/period
        # that are reconciled after FY/period
        if next_period_ids:
            subquery = "OR reconcile_id IN " \
                "(SELECT reconcile_id FROM account_move_line " \
                "WHERE period_id IN %s " \
                "AND reconcile_id IS NOT NULL)" % str(
                    tuple(next_period_ids)).replace(',)', ')')
        else:
            subquery = None

        query_end = 'WHERE m.company_id = %s ' \
            'AND a.type = %s ' + move_selection + \
            'AND (l.reconcile_id IS NULL ' + (subquery or '') + ') ' \
            'AND (l.debit+l.credit) != 0 ' \
            'ORDER BY a_code, p_name, p_id, l_date'

        if result_selection == 'customer':
            reports = [report_ar]
        elif result_selection == 'supplier':
            reports = [report_ap]
        else:
            reports = [report_ar, report_ap]

        for report in reports:

            cr.execute(query_start + query_end, (company_id, report['type']))
            all_lines = cr.dictfetchall()
            partners = []

            if all_lines:

                # add reference of corresponding legal document
                def lines_map(x):
                    if x['j_type'] in ['sale', 'sale_refund',
                                       'purchase', 'purchase_refund']:
                        x.update({
                            'docname': x['inv_number'] or x['voucher_number']
                        })
                    elif x['j_type'] in ['bank', 'cash']:
                        x.update({
                            'docname': x['st_number'] or x['voucher_number']
                        })
                    else:
                        x.update({'docname': x['move_name']})
                map(lines_map, all_lines)

                # insert a flag in every line to indicate the end of a partner
                # this flag can be used to draw a full line between partners
                for cnt in range(len(all_lines)-1):
                    if all_lines[cnt]['p_id'] != all_lines[cnt+1]['p_id']:
                        all_lines[cnt]['draw_line'] = 1
                    else:
                        all_lines[cnt]['draw_line'] = 0
                all_lines[-1]['draw_line'] = 1

                p_map = map(
                    lambda x: {
                        'p_id': x['p_id'],
                        'p_name': x['p_name'],
                        'p_ref': x['p_ref']},
                    all_lines)
                for p in p_map:
                    # remove duplicates while preserving list order
                    if p['p_id'] not in map(
                            lambda x: x.get('p_id', None), partners):
                        partners.append(p)
                        partner_lines = filter(
                            lambda x: x['p_id'] == p['p_id'], all_lines)
                        p.update({'lines': partner_lines})
                        debits = map(
                            lambda x: x['debit'] or 0.0, partner_lines)
                        sum_debit = reduce(lambda x, y: x + y, debits)
                        credits = map(
                            lambda x: x['credit'] or 0.0, partner_lines)
                        sum_credit = reduce(lambda x, y: x + y, credits)
                        balance = sum_debit - sum_credit
                        p.update(
                            {'d': sum_debit,
                             'c': sum_credit,
                             'b': balance})
                report.update({'partners': partners})

                sum_debit = 0
                sum_credit = 0
                acc_lines = filter(
                    lambda x: x['a_type'] == report['type'], all_lines)
                debits = map(lambda x: x['debit'] or 0.0, acc_lines)
                if debits:
                    sum_debit = reduce(lambda x, y: x + y, debits)
                credits = map(lambda x: x['credit'] or 0.0, acc_lines)
                if credits:
                    sum_credit = reduce(lambda x, y: x + y, credits)
                balance = sum_debit - sum_credit
                report.update({'d': sum_debit, 'c': sum_credit, 'b': balance})

        reports = filter(lambda x: x.get('partners'), reports)
        if not reports:
            raise orm.except_orm(
                _('No Data Available'),
                _('No records found for your selection!'))

        self.localcontext.update({
            'report_info': report_info,
            'reports': reports,
            })
        super(partner_open_arap_print, self).set_context(
            objects, data, ids, report_type)

    def formatLang(self, value, digits=None, date=False, date_time=False,
                   grouping=True, monetary=False, dp=False,
                   currency_obj=False):
        if isinstance(value, (float, int)) and not value:
            return ''
        else:
            return super(partner_open_arap_print, self).formatLang(
                value, digits, date, date_time, grouping,
                monetary, dp, currency_obj)

report_sxw.report_sxw(
    'report.account.partner.open.arap.period.print',
    'account.period',
    'addons/account_open_receivables_payables_xls/'
    'report/account_partner_open_arap.rml',
    parser=partner_open_arap_print, header=False)
