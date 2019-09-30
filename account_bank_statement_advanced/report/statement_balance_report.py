# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from functools import reduce


class StatementBalanceReport(models.AbstractModel):
    _name = 'report.account_bank_statement_advanced.statement_balance_report'
    _description = 'Bank Statement Balances Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        journal_ids = data['journal_ids']
        company = self.env.user.company_id
        if not journal_ids:
            journals = self.env['account.journal'].search(
                [('type', '=', 'bank'),
                 ('company_id', '=', company.id)])
            journal_ids = journals.ids
        if not journal_ids:
            raise UserError(
                _('No financial journals found for your company!'))
        self.env.cr.execute(
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
            (data['date_balance'], tuple(journal_ids)))
        lines = self.env.cr.dictfetchall()
        currency_ids = set([l['j_curr_id'] for l in lines])
        currencies = self.env['res.currency'].browse(currency_ids)
        currency_dict = {c.id: c for c in currencies}
        [l.update({'currency': currency_dict[l['j_curr_id']]}) for l in lines]
        totals = []
        for currency in currencies:
            lines_currency = [x for x in lines if x['currency'] == currency]
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
            self.env.user, datetime.now()).strftime('%Y-%m-%d %H:%M')

        return {
            'lines': lines,
            'totals': totals,
            'date_balance': data['date_balance'],
            'report_date': report_date,
        }
