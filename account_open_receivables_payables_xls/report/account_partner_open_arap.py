# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import api, fields, models, _
from openerp.exceptions import except_orm
from openerp.report import report_sxw

import logging
_logger = logging.getLogger(__name__)


class AccountPartnerOpenArap(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(AccountPartnerOpenArap, self).__init__(
            cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'formatLang_zero2blank': self.formatLang_zero2blank,
        })

    def set_context(self, wiz, data, ids, report_type=None):
        self.env = api.Environment(self.cr, self.uid, self.context)
        posted = wiz.target_move == 'posted' and True or False
        period_code = wiz.period_id.code
        title_prefix = _('Period') + ' %s : ' % period_code
        title_short_prefix = period_code
        digits = self.env['decimal.precision'].precision_get('Account')

        # perform query on selected period as well as preceding periods.
        period_query_ids = wiz.period_id.search(
            [('date_stop', '<=', wiz.period_id.date_start),
             ('company_id', '=', wiz.company_id.id)]).ids
        period_query_ids += [wiz.period_id.id]
        # find periods to select move_lines
        # that are reconciled after period
        next_period_ids = wiz.period_id.search(
            [('date_stop', '>', wiz.period_id.date_stop),
             ('company_id', '=', wiz.company_id.id)]).ids

        report_ar = {
            'type': 'receivable',
            'title': title_prefix + _('Open Receivables'),
            'title_short': title_short_prefix + ', ' + _('AR')}
        report_ap = {
            'type': 'payable',
            'title': title_prefix + _('Open Payables'),
            'title_short': title_short_prefix + ', ' + _('AP')}
        report_other = {
            'type': 'open_items',
            'title': title_prefix + _('Open Items'),
            'title_short': title_short_prefix + ', ' + _('Open Items')}

        select_extra, join_extra, where_extra = \
            self.env['res.partner']._xls_query_extra()

        # CASE statement on due date since standard Odoo accounting
        # allows to change the date_maturity in the accounting entries
        # on confirmed invoices (when using the account_cancel module).
        # The CASE statement gives accounting entries priority
        # over the invoice field.
        query_start = (
            "SELECT l.move_id AS m_id, l.id AS l_id, "
            "l.date AS l_date, "
            "m.name AS move_name, m.date AS m_date, "
            "a.id AS a_id, a.code AS a_code, a.type AS a_type, "
            "j.id AS j_id, j.code AS j_code, j.type AS j_type, "
            "p.id AS p_id, p.name AS p_name, p.ref AS p_ref, "
            "l.name AS l_name, "
            "l.debit, l.credit, "
            "(CASE WHEN l.date_maturity IS NOT NULL THEN l.date_maturity "
            "ELSE ai.date_due END) AS date_due, "
            "l.reconcile_id, r.name AS r_name, "
            "l.reconcile_partial_id, rp.name AS rp_name, "
            "ai.internal_number AS inv_number, b.name AS st_number, "
            "ai.supplier_invoice_number as sup_inv_nr, "
            "v.number AS voucher_number " + select_extra +
            "FROM account_move_line l "
            "INNER JOIN account_journal j ON l.journal_id = j.id "
            "INNER JOIN account_move m ON l.move_id = m.id "
            "INNER JOIN account_account a ON l.account_id = a.id "
            "INNER JOIN account_period ap ON l.period_id = ap.id "
            "LEFT OUTER JOIN account_invoice ai ON ai.move_id = m.id "
            "LEFT OUTER JOIN account_voucher v ON v.move_id = m.id "
            "LEFT OUTER JOIN account_bank_statement b "
            "ON l.statement_id = b.id "
            "LEFT OUTER JOIN res_partner p ON l.partner_id = p.id "
            "LEFT OUTER JOIN account_move_reconcile r "
            "ON l.reconcile_id = r.id "
            "LEFT OUTER JOIN account_move_reconcile rp "
            "ON l.reconcile_partial_id = rp.id " + join_extra)

        if posted:
            move_selection = "AND m.state = 'posted' "
            report_info = _('All Posted Entries')
        else:
            move_selection = ''
            report_info = _('All Entries')

        if wiz.partner_id:
            move_selection += "AND l.partner_id = %s " % wiz.partner_id.id

        move_selection += "AND ap.id in %s " % str(
            tuple(period_query_ids)).replace(',)', ')')

        if wiz.account_ids:
            account_selection = "AND a.id IN %s " % str(
                wiz.account_ids._ids).replace(',)', ')')
        else:
            account_selection = "AND a.type = '%s' "

        # define subquery to select move_lines within FY/period
        # that are reconciled after FY/period
        if next_period_ids:
            subquery = (
                "OR reconcile_id IN "
                "(SELECT reconcile_id FROM account_move_line "
                "WHERE period_id IN %s "
                "AND reconcile_id IS NOT NULL) "
            ) % str(tuple(next_period_ids)).replace(',)', ')')
        else:
            subquery = ''

        query_end = (
            'WHERE m.company_id = %s ' % wiz.company_id.id +
            account_selection + move_selection +
            'AND (l.reconcile_id IS NULL ' + subquery + ') '
            'AND (l.debit+l.credit) != 0 ' + where_extra +
            'ORDER BY a_code, p_name, p_id, l_date')

        if wiz.result_selection == 'customer':
            reports = [report_ar]
        elif wiz.result_selection == 'supplier':
            reports = [report_ap]
        elif wiz.result_selection == 'customer_supplier':
            reports = [report_ar, report_ap]
        else:
            reports = [report_other]

        for report in reports:
            query = query_start + query_end
            if report['type'] != 'open_items':
                query = query % report['type']
            self.cr.execute(query)
            lines = self.cr.dictfetchall()
            partners = []

            if lines:

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
                map(lines_map, lines)

                p_map = map(
                    lambda x: {
                        'p_id': x['p_id'],
                        'p_name': x['p_name'],
                        'p_ref': x['p_ref']},
                    lines)
                for p in p_map:
                    # remove duplicates while preserving list order
                    if p['p_id'] not in map(
                            lambda x: x.get('p_id', None), partners):
                        partners.append(p)
                        partner_lines = filter(
                            lambda x: x['p_id'] == p['p_id'], lines)
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
                debits = map(lambda x: x['debit'] or 0.0, lines)
                if debits:
                    sum_debit = reduce(lambda x, y: x + y, debits)
                    sum_debit = round(sum_debit, digits)
                credits = map(lambda x: x['credit'] or 0.0, lines)
                if credits:
                    sum_credit = reduce(lambda x, y: x + y, credits)
                    sum_credit = round(sum_credit, digits)
                balance = sum_debit - sum_credit
                report.update({'d': sum_debit, 'c': sum_credit, 'b': balance})

        reports = filter(lambda x: x.get('partners'), reports)
        if not reports:
            raise except_orm(
                _('No Data Available'),
                _('No records found for your selection!'))

        report_date = fields.Datetime.context_timestamp(wiz, datetime.now())
        self.localcontext.update({
            'report_info': report_info,
            'report_date': report_date,
            'reports': reports,
        })
        super(AccountPartnerOpenArap, self).set_context(
            wiz, data, ids, report_type=report_type)

    def formatLang_zero2blank(self, value, digits=None, date=False,
                              date_time=False, grouping=True, monetary=False,
                              dp=False, currency_obj=False):
        if isinstance(value, (float, int)) and not value:
            return ''
        else:
            return super(AccountPartnerOpenArap, self).formatLang(
                value, digits=digits, date=date, date_time=date_time,
                grouping=grouping, monetary=monetary, dp=dp,
                currency_obj=currency_obj)


class WrappedOpenArapPrint(models.AbstractModel):
    _name = 'report.account_open_receivables_payables_xls.report_open_arap'
    _inherit = 'report.abstract_report'
    _template = 'account_open_receivables_payables_xls.report_open_arap'
    _wrapped_report_class = AccountPartnerOpenArap
