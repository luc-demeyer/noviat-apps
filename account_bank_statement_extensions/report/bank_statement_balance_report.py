# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
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
from openerp.osv import orm
from openerp.tools.translate import _
from openerp import pooler
import logging
_logger = logging.getLogger(__name__)


class bank_statement_balance_report(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        #_logger.warn('set_context, objects = %s, data = %s, ids = %s', objects, data, ids)
        cr = self.cr
        uid = self.uid
        context = self.context
        curr_obj = self.pool.get('res.currency')
        date_balance = data['date_balance']
        journal_ids = data['journal_ids']
        cr.execute("SELECT s.name AS s_name, s.date AS s_date, j.code AS j_code, "
            "s.balance_end_real AS s_balance, coalesce(jcu.id,ccu.id) as j_curr_id "
            "FROM account_bank_statement s "
            "INNER JOIN account_journal j ON s.journal_id = j.id "
            "INNER JOIN res_company co ON j.company_id = co.id "
            "LEFT OUTER JOIN res_currency jcu ON j.currency = jcu.id "
            "LEFT OUTER JOIN res_currency ccu ON co.currency_id = ccu.id "
            "INNER JOIN "
                "(SELECT journal_id, max(date) AS max_date FROM account_bank_statement "
                    "WHERE date <= %s GROUP BY journal_id) d "
                    "ON (s.journal_id = d.journal_id AND s.date = d.max_date) "
            "WHERE s.journal_id in %s "
            "ORDER BY j_curr_id, j.code", (date_balance, tuple(journal_ids)))
        lines = cr.dictfetchall()
        [x.update({'currency': curr_obj.browse(cr, uid, x['j_curr_id'])}) for x in lines]
        currencies = list(set([x['currency'] for x in lines]))
        totals = []
        for currency in currencies:
            lines_currency = filter(lambda x: x['currency']==currency, lines)
            total_amount = reduce(lambda x,y: x+y, [x['s_balance'] for x in lines_currency])
            totals.append({
                'currency': currency,
                'total_amount': total_amount, 
            })
        if not lines:
            raise orm.except_orm(_('No Data Available'), _('No records found for your selection!'))

        self.localcontext.update({
            'lines': lines,
            'totals': totals,
            'date_balance': date_balance,
        })
        super(bank_statement_balance_report, self).set_context(objects, data, ids, report_type=report_type)

    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(bank_statement_balance_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
        })
        self.context = context
 
report_sxw.report_sxw(
    'report.bank.statement.balance.report',
    'account.bank.statement',
    'addons/account_bank_statement_extensions/report/bank_statement_balance_report.rml',
    parser=bank_statement_balance_report,
    header='internal'
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
