# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo import fields, models, _
from openerp.report import report_sxw
from odoo.exceptions import UserError


class BankStatementBalanceReport(report_sxw.rml_parse):

    def set_context(self, wiz, data, ids, report_type=None):
        journals = wiz.journal_ids or \
            wiz.env['account.journal'].search([('type', '=', 'bank')])
        self.cr.execute(
            "SELECT s.name AS s_name, s.date AS s_date, j.code AS j_code, "
            "s.balance_end_real AS s_balance, "
            "COALESCE(jcu.id,ccu.id) AS j_curr_id "
            "FROM account_bank_statement s "
            "INNER JOIN account_journal j ON s.journal_id = j.id "
            "INNER JOIN res_company co ON j.company_id = co.id "
            "LEFT OUTER JOIN res_currency jcu ON j.currency_id = jcu.id "
            "LEFT OUTER JOIN res_currency ccu ON co.currency_id = ccu.id "
            "INNER JOIN "
            "  (SELECT journal_id, max(date) AS max_date "
            "   FROM account_bank_statement "
            "   WHERE date <= %s GROUP BY journal_id) d "
            "   ON (s.journal_id = d.journal_id AND s.date = d.max_date) "
            "WHERE s.journal_id IN %s "
            "ORDER BY j_curr_id, j.code",
            (wiz.date_balance, journals._ids))
        lines = self.cr.dictfetchall()
        [x.update(
            {'currency': wiz.env['res.currency'].browse(x['j_curr_id'])})
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
            raise UserError(_('No records found for your selection!'))

        report_date = fields.Datetime.context_timestamp(
            wiz.env.user, datetime.now()).strftime('%Y-%m-%d %H:%M')

        self.localcontext.update({
            'lines': lines,
            'totals': totals,
            'date_balance': wiz.date_balance,
            'report_date': report_date,
        })
        super(BankStatementBalanceReport, self).set_context(
            wiz, data, ids, report_type=report_type)


class ReportBankStatementBalances(models.AbstractModel):
    _name = 'report.account.report_statement_balances'
    _inherit = 'report.abstract_report'
    _template = 'account.report_statement_balances'
    _wrapped_report_class = BankStatementBalanceReport
