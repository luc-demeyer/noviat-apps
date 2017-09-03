# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.report import report_sxw
from openerp import models, _
from openerp.exceptions import Warning as UserError


class bank_statement_balance_report(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        data = objects[0]
        cr = data._cr
        uid = data._uid
        context = data._context
        date_balance = data['date_balance']
        journal_ids = [x.id for x in data['journal_ids']]
        if not journal_ids:
            raise UserError(_('No Financial Journals selected!'))
        cr.execute(
            "SELECT s.name AS s_name, s.date AS s_date, j.code AS j_code, "
            "s.balance_end_real AS s_balance, "
            "coalesce(jcu.id,ccu.id) as j_curr_id "
            "FROM account_bank_statement s "
            "INNER JOIN account_journal j ON s.journal_id = j.id "
            "INNER JOIN res_company co ON j.company_id = co.id "
            "LEFT OUTER JOIN res_currency jcu ON j.currency = jcu.id "
            "LEFT OUTER JOIN res_currency ccu ON co.currency_id = ccu.id "
            "INNER JOIN "
            "  (SELECT journal_id, max(date) AS max_date "
            "   FROM account_bank_statement "
            "   WHERE date <= %s GROUP BY journal_id) d "
            "   ON (s.journal_id = d.journal_id AND s.date = d.max_date) "
            "WHERE s.journal_id in %s "
            "ORDER BY j_curr_id, j.code", (date_balance, tuple(journal_ids)))
        lines = cr.dictfetchall()
        [x.update(
            {'currency': data.env['res.currency'].browse(x['j_curr_id'])})
         for x in lines]
        currencies = list(set([x['currency'] for x in lines]))
        totals = []
        for currency in currencies:
            lines_currency = filter(lambda x: x['currency'] == currency, lines)
            total_amount = reduce(
                lambda x, y: x + y,
                [x['s_balance'] for x in lines_currency])
            totals.append({
                'currency': currency,
                'total_amount': total_amount,
            })
        if not lines:
            raise Warning(_('No records found for your selection!'))

        report_date = datetime_field.context_timestamp(
            cr, uid, datetime.now(), context
        ).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        self.localcontext.update({
            'lines': lines,
            'totals': totals,
            'date_balance': date_balance,
            'report_date': report_date,
        })
        super(bank_statement_balance_report, self).set_context(
            objects, data, ids, report_type=report_type)


class report_bankstatementbalance(models.AbstractModel):
    _name = 'report.account_bank_statement_advanced.report_statement_balances'
    _inherit = 'report.abstract_report'
    _template = 'account_bank_statement_advanced.report_statement_balances'
    _wrapped_report_class = bank_statement_balance_report
