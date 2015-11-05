# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010-2015 Noviat nv/sa (www.noviat.com).
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

from datetime import datetime
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
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
        self.context = context
        self.localcontext.update({
            'formatLang_zero2blank': self.formatLang_zero2blank,
            })

    def set_context(self, objects, data, ids, report_type=None):
        cr = self.cr
        uid = self.uid
        context = self.context

        period_obj = self.pool['account.period']
        partner_obj = self.pool['res.partner']

        posted = (data['target_move'] == 'posted') and True or False
        result_selection = data['result_selection']
        company_id = data['company_id']
        period_id = data['period_id']
        period = period_obj.browse(cr, uid, period_id, context=context)
        period_code = period.code
        title_prefix = _('Period') + ' %s : ' % period_code
        title_short_prefix = period_code
        digits = self.pool['decimal.precision'].precision_get(
            cr, uid, 'Account')

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

        select_extra, join_extra, where_extra = \
            partner_obj._xls_query_extra(cr, uid, context=context)

        # CASE statement on due date since standard Odoo accounting
        # allows to change the date_maturity in the accounting entries
        # on confirmed invoices (when using the account_cancel module).
        # The CASE statement gives accounting entries priority
        # over the invoice field.
        query_start = "SELECT l.move_id AS m_id, l.id AS l_id, " \
            "l.date AS l_date, " \
            "m.name AS move_name, m.date AS m_date, " \
            "a.id AS a_id, a.code AS a_code, a.type AS a_type, " \
            "j.id AS j_id, j.code AS j_code, j.type AS j_type, " \
            "p.id AS p_id, p.name AS p_name, p.ref AS p_ref, " \
            "l.name AS l_name, " \
            "l.debit, l.credit, " \
            "(CASE WHEN l.date_maturity IS NOT NULL THEN l.date_maturity " \
            "ELSE ai.date_due END) AS date_due," \
            "l.reconcile_id, r.name AS r_name, " \
            "l.reconcile_partial_id, rp.name AS rp_name, " \
            "ai.internal_number AS inv_number, b.name AS st_number, " \
            "ai.supplier_invoice_number as sup_inv_nr, " \
            "v.number AS voucher_number " + select_extra + \
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
            "ON l.reconcile_partial_id = rp.id " \
            + join_extra

        if posted:
            move_selection = "AND m.state = 'posted' "
            report_info = _('All Posted Entries')
        else:
            move_selection = ''
            report_info = _('All Entries')

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
            + where_extra + \
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
                        sum_debit = round(sum_debit, digits)
                        credits = map(
                            lambda x: x['credit'] or 0.0, partner_lines)
                        sum_credit = reduce(lambda x, y: x + y, credits)
                        sum_credit = round(sum_credit, digits)
                        balance = sum_debit - sum_credit
                        p.update(
                            {'d': sum_debit,
                             'c': sum_credit,
                             'b': balance})
                report.update({'partners': partners})

                sum_debit = 0.0
                sum_credit = 0.0
                acc_lines = filter(
                    lambda x: x['a_type'] == report['type'], all_lines)
                debits = map(lambda x: x['debit'] or 0.0, acc_lines)
                if debits:
                    sum_debit = reduce(lambda x, y: x + y, debits)
                    sum_debit = round(sum_debit, digits)
                credits = map(lambda x: x['credit'] or 0.0, acc_lines)
                if credits:
                    sum_credit = reduce(lambda x, y: x + y, credits)
                    sum_credit = round(sum_credit, digits)
                balance = sum_debit - sum_credit
                report.update({'d': sum_debit, 'c': sum_credit, 'b': balance})

        reports = filter(lambda x: x.get('partners'), reports)
        if not reports:
            raise orm.except_orm(
                _('No Data Available'),
                _('No records found for your selection!'))

        report_date = datetime_field.context_timestamp(
            cr, uid, datetime.now(), context
            ).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        self.localcontext.update({
            'report_info': report_info,
            'report_date': report_date,
            'reports': reports,
            })
        super(partner_open_arap_print, self).set_context(
            objects, data, ids, report_type=report_type)

    def formatLang_zero2blank(self, value, digits=None, date=False,
                              date_time=False, grouping=True, monetary=False,
                              dp=False, currency_obj=False):
        if isinstance(value, (float, int)) and not value:
            return ''
        else:
            return super(partner_open_arap_print, self).formatLang(
                value, digits=digits, date=date, date_time=date_time,
                grouping=grouping, monetary=monetary, dp=dp,
                currency_obj=currency_obj)


class wrapped_vat_declaration_print(orm.AbstractModel):
    _name = 'report.account_open_receivables_payables_xls.report_open_arap'
    _inherit = 'report.abstract_report'
    _template = 'account_open_receivables_payables_xls.report_open_arap'
    _wrapped_report_class = partner_open_arap_print
