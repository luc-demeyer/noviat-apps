# Copyright 2009-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from functools import reduce
import logging

from odoo import models
from odoo.tools.translate import translate

_logger = logging.getLogger(__name__)

IR_TRANSLATION_NAME = 'account.partner.open.items'


class AccountPartnerOpenItemsXlsx(models.AbstractModel):
    _name = 'report.account_partner_open_items_xlsx.partner_open_items_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, workbook, data, partners):

        wiz = self.env['wiz.partner.open.items'].browse(data['wiz_id'])
        posted = wiz.target_move == 'posted' and True or False
        digits = self.env['decimal.precision'].precision_get('Account')
        report_ar = {
            'type': 'receivable',
            'title_short': self._('AR'),
        }
        report_ap = {
            'type': 'payable',
            'title_short': self._('AP'),
        }
        report_other = {
            'type': 'open_items',
            'title_short': self._('Open Items'),
        }
        select_extra, join_extra, where_extra = \
            self.env['res.partner']._xls_query_extra()

        if wiz.add_reconcile:
            select_reconcile_details = (
                "CASE WHEN l.balance > 0 "
                "THEN "
                " ARRAY(SELECT prl.id FROM account_partial_reconcile pr "
                "  INNER JOIN account_move_line prl "
                "    ON pr.credit_move_id = prl.id "
                "  WHERE pr.debit_move_id = l.id "
                "  AND prl.date <= '{0}') "
                "ELSE "
                " ARRAY(SELECT prl.id FROM account_partial_reconcile pr "
                "  INNER JOIN account_move_line prl "
                "    ON pr.debit_move_id = prl.id "
                "  WHERE pr.credit_move_id = l.id "
                "  AND prl.date <= '{0}') "
                "END AS prl_ids, "
            ).format(wiz.date_at)
        else:
            select_reconcile_details = ''

        if wiz.add_currency:
            select_currency = (
                "c.name AS currency, l.amount_currency, "
                "CASE WHEN l.balance > 0 "
                "     THEN (SELECT COALESCE(SUM(pr.amount_currency), 0) "
                "           FROM account_partial_reconcile pr "
                "           INNER JOIN account_move_line prl "
                "             ON pr.credit_move_id = prl.id "
                "           WHERE pr.debit_move_id = l.id "
                "           AND prl.date <= '{0}') "
                "     ELSE (SELECT COALESCE(SUM(-pr.amount_currency), 0) "
                "           FROM account_partial_reconcile pr "
                "           INNER JOIN account_move_line prl "
                "             ON pr.debit_move_id = prl.id "
                "           WHERE pr.credit_move_id = l.id "
                "           AND prl.date <= '{0}') "
                "     END AS amount_currency_reconciled, "
            ).format(wiz.date_at)
        else:
            select_currency = ''

        # CASE statement on due date since standard Odoo accounting
        # allows to change the date_maturity in the accounting entries
        # on confirmed invoices.
        # The CASE statement gives accounting entries priority
        # over the invoice field.
        query_start = (
            "SELECT DISTINCT(l.id) AS l_id, "
            "l.date AS l_date, l.move_id AS m_id, "
            "m.name AS move_name, m.date AS m_date, "
            "a.id AS a_id, a.code AS a_code, aat.type AS a_type, "
            "j.id AS j_id, j.code AS j_code, j.type AS j_type, "
            "p.id AS p_id, p.name AS p_name, p.ref AS p_ref, "
            "l.name AS l_name, l.balance AS amount_original, "
            + select_currency +
            "CASE WHEN l.date_maturity IS NOT NULL "
            "     THEN l.date_maturity "
            "     ELSE ai.date_due "
            "     END AS date_due, "
            "l.full_reconcile_id, fr.name AS fr_name, "
            "ai.number AS inv_number, b.name AS st_number, "
            "ai.reference AS sup_inv_nr, ai.origin AS origin, "
            + select_reconcile_details +
            "CASE WHEN l.balance > 0 "
            "     THEN (SELECT COALESCE(SUM(pr.amount), 0) "
            "           FROM account_partial_reconcile pr "
            "           INNER JOIN account_move_line prl "
            "             ON pr.credit_move_id = prl.id "
            "           WHERE pr.debit_move_id = l.id "
            "           AND prl.date <= '{0}') "
            "     ELSE (SELECT COALESCE(SUM(-pr.amount), 0) "
            "           FROM account_partial_reconcile pr "
            "           INNER JOIN account_move_line prl "
            "             ON pr.debit_move_id = prl.id "
            "           WHERE pr.credit_move_id = l.id "
            "           AND prl.date <= '{0}') "
            "     END AS amount_reconciled "
            + select_extra +
            "FROM account_move_line l "
            "INNER JOIN account_journal j ON l.journal_id = j.id "
            "INNER JOIN account_move m ON l.move_id = m.id "
            "INNER JOIN account_account a ON l.account_id = a.id "
            "INNER JOIN account_account_type aat ON a.user_type_id = aat.id "
            "LEFT OUTER JOIN res_currency c ON a.currency_id = c.id "
            "LEFT OUTER JOIN account_invoice ai ON ai.move_id = m.id "
            "LEFT OUTER JOIN account_bank_statement b "
            "ON l.statement_id = b.id "
            "LEFT OUTER JOIN res_partner p ON l.partner_id = p.id "
            "LEFT OUTER JOIN account_full_reconcile fr "
            "ON l.full_reconcile_id = fr.id "
            "LEFT OUTER JOIN account_partial_reconcile pr "
            "ON pr.debit_move_id = l.id OR pr.credit_move_id = l.id "
            + join_extra
        ).format(wiz.date_at)

        move_selection = "AND l.date <= '%s' " % wiz.date_at
        if posted:
            move_selection += "AND m.state = 'posted' "

        if wiz.account_ids:
            account_selection = "AND a.id IN %s " % str(
                wiz.account_ids._ids).replace(',)', ')')
        else:
            account_selection = "AND aat.type = '%s' "

        if wiz.partner_select == 'select':
            partner_selection = "AND p.id IN %s " % str(
                partners._ids).replace(',)', ')')
        else:
            partner_selection = ''

        # include journal items reconciled after wiz.date_at
        reconciled_after = (
            "OR (l.balance > 0 AND l.full_reconcile_id IN "
            " (SELECT pr.full_reconcile_id FROM account_partial_reconcile pr "
            "  INNER JOIN account_move_line prl ON pr.credit_move_id = prl.id "
            "  WHERE pr.debit_move_id = l.id "
            "  AND prl.date > '{0}')) "
            "OR (l.balance < 0 AND l.full_reconcile_id IN "
            " (SELECT pr.full_reconcile_id FROM account_partial_reconcile pr "
            "  INNER JOIN account_move_line prl ON pr.debit_move_id = prl.id "
            "  WHERE pr.credit_move_id = l.id "
            "  AND prl.date > '{0}')) "
        ).format(wiz.date_at)

        query_end = (
            "WHERE m.company_id = %s " % wiz.company_id.id +
            move_selection + account_selection + partner_selection +
            """
    AND (
      (l.full_reconcile_id IS NULL AND
         (pr.id IS NULL
          OR CASE WHEN l.id = pr.debit_move_id
               THEN (SELECT date FROM account_move_line WHERE id = pr.credit_move_id)
               ELSE (SELECT date FROM account_move_line WHERE id = pr.debit_move_id)
             END > '{0}'
          OR COALESCE(pr.amount, 0) < abs(l.balance)
         )
      )
            """.format(wiz.date_at)
            + reconciled_after + ") "
            "AND l.balance != 0 " + where_extra +
            "ORDER BY a_code")

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
            self.env.cr.execute(query)
            lines = self.env.cr.dictfetchall()
            partners = []

            if lines:

                # add reference of corresponding legal document
                def lines_map(x):
                    if x['j_type'] in ['sale', 'purchase']:
                        x.update({
                            'docname': x['inv_number']
                            or x['move_name'] or '*{}'.format(x['m_id'])
                        })
                    elif x['j_type'] in ['bank', 'cash']:
                        x.update({
                            'docname': x['st_number']
                            or x['move_name'] or '*{}'.format(x['m_id'])
                        })
                    else:
                        x.update({
                            'docname': x['move_name']
                            or '*{}'.format(x['m_id'])})
                list(map(lines_map, lines))
                lines.sort(
                    key=lambda x: (
                        x['l_date'],
                        x['docname'] and x['docname'].lower()))

                p_map = [{
                        'p_id': x['p_id'],
                        'p_name': x['p_name'],
                        'p_ref': x['p_ref']} for x in lines]
                # sort with p_id None entries at the end
                p_map.sort(
                    key=lambda x: (
                        not x['p_id'],
                        x['p_name'] and x['p_name'].lower()))
                for p in p_map:
                    # remove duplicates while preserving list order
                    if p['p_id'] not in [x.get('p_id', None)
                                         for x in partners]:
                        partners.append(p)
                        partner_lines = [x for x in lines
                                         if x['p_id'] == p['p_id']]
                        p.update({'lines': partner_lines})
                        original_amounts = [x['amount_original']
                                            for x in partner_lines]
                        amount_original = reduce(
                            lambda x, y: x + y, original_amounts)
                        amount_original = round(amount_original, digits)
                        p['amount_original'] = amount_original
                        reconciled_amounts = [x['amount_reconciled']
                                              for x in partner_lines]
                        amount_reconciled = reduce(
                            lambda x, y: x + y, reconciled_amounts)
                        amount_reconciled = round(amount_reconciled, digits)
                        p['amount_reconciled'] = amount_reconciled
                        if not p['p_id']:
                            p_full_name = self._("No partner allocated")
                        else:
                            p_full_name = p['p_name'] or self._('n/a')
                            if p['p_ref']:
                                p_full_name += ' (%s)' % p['p_ref']
                        p['p_full_name'] = p_full_name
                report.update({'partners': partners})

        ws_params = []
        for report in reports:
            if not report.get('partners'):
                title = self._get_report_title(data, wiz, report, 'empty')
                ws_params.append({
                    'ws_name': report['title_short'],
                    'generate_ws_method': '_empty_report',
                    'title': title,
                    'wiz': wiz,
                })
                continue

            title = self._get_report_title(data, wiz, report, 'overview')
            wl = self.env['res.partner'].\
                _xls_open_items_overview_fields(report)
            col_specs = self._get_overview_template()
            col_specs.update(
                self.env['res.partner']._xls_open_items_overview_template(
                    report)
            )
            ws_params_overview = {
                'ws_name': report['title_short'],
                'generate_ws_method': '_overview_report',
                'title': title,
                'wanted_list': wl,
                'col_specs': col_specs,
                'report': report,
                'wiz': wiz,
            }
            ws_params.append(ws_params_overview)

            title = self._get_report_title(data, wiz, report, 'details')
            wl = self.env['res.partner'].\
                _xls_open_items_details_fields(report)
            if wiz.add_currency:
                wl.extend(
                    ['currency', 'amount_currency',
                     'amount_currency_reconciled'])
            if wiz.add_reconcile:
                wl.append('rec_details')
            col_specs = self._get_details_template()
            col_specs.update(
                self.env['res.partner']._xls_open_items_details_template(
                    report)
            )
            ws_params_details = {
                'ws_name': report['title_short'] + ' ' + self._('Details'),
                'generate_ws_method': '_details_report',
                'title': title,
                'wanted_list': wl,
                'col_specs': col_specs,
                'report': report,
                'wiz': wiz,
            }
            ws_params.append(ws_params_details)

        return ws_params

    def _get_report_title(self, data, wiz, report, report_type):
        s = '  -  '
        title = wiz.company_id.name + s + wiz.date_at + ': '
        if report['type'] == 'receivable':
            title += self._('Open Receivables')
        elif report['type'] == 'payable':
            title += self._('Open Payables')
        else:
            title += self._('Open Items')
        if report_type == 'overview':
            title += s + self._('Overview')
        elif report_type == 'details':
            title += s + self._('Details')
        if wiz.target_move == 'posted':
            title += s + self._('All Posted Entries')
        else:
            title += s + self._('All Entries')
        title += s + wiz.company_id.currency_id.name
        return title

    def _report_title(self, ws, row_pos, ws_params, data):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _empty_report(self, workbook, ws, ws_params, data, partners):
        row_pos = 0
        row_pos = self._report_title(ws, row_pos, ws_params, data)
        no_items = self._("No Open Items found for your selection")
        ws.write_string(row_pos, 0, no_items, self.format_left_bold)

    def _get_overview_template(self):

        template = {
            'partner': {
                'header': {
                    'type': 'string',
                    'value': self._('Partner'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render(
                        "p['p_id'] and (p['p_name'] or '-') "
                        "or p['p_full_name']"),
                },
                'width': 44,
            },
            'partner_ref': {
                'header': {
                    'type': 'string',
                    'value': self._('Partner Reference'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render("p['p_ref'] or ''"),
                },
                'width': 22,
            },
            'amount_original': {
                'header': {
                    'value': self._('Original'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("p['amount_original']"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("amount_original_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'amount_reconciled': {
                'header': {
                    'value': self._('Reconciled'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("p['amount_reconciled']"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("amount_reconciled_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'balance': {
                'header': {
                    'value': self._('Balance'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'formula',
                    'value': self._render("bal_formula"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("bal_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
        }

        return template

    def _overview_report(self, workbook, ws, ws_params, data, partners):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params)

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        report = ws_params['report']
        wanted_list = ws_params['wanted_list']
        orig_pos = ('amount_original' in wanted_list
                    and wanted_list.index('amount_original'))
        rec_pos = ('amount_reconciled' in wanted_list
                   and wanted_list.index('amount_reconciled'))
        for partner in report['partners']:
            orig_cell = self._rowcol_to_cell(row_pos, orig_pos)
            rec_cell = self._rowcol_to_cell(row_pos, rec_pos)
            bal_formula = orig_cell + '-' + rec_cell
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={
                    'p': partner,
                    'bal_formula': bal_formula,
                },
                default_format=self.format_tcell_left)

        p_cnt = len(report['partners'])
        orig_start = self._rowcol_to_cell(row_pos - p_cnt, orig_pos)
        orig_stop = self._rowcol_to_cell(row_pos - 1, orig_pos)
        orig_formula = 'SUM(%s:%s)' % (orig_start, orig_stop)
        rec_start = self._rowcol_to_cell(row_pos - p_cnt, rec_pos)
        rec_stop = self._rowcol_to_cell(row_pos - 1, rec_pos)
        rec_formula = 'SUM(%s:%s)' % (rec_start, rec_stop)
        orig_cell = self._rowcol_to_cell(row_pos, orig_pos)
        rec_cell = self._rowcol_to_cell(row_pos, rec_pos)
        bal_formula = orig_cell + '-' + rec_cell
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'amount_original_formula': orig_formula,
                'amount_reconciled_formula': rec_formula,
                'bal_formula': bal_formula,
            },
            default_format=self.format_theader_yellow_left)

    def _get_details_template(self):

        template = {
            'document': {
                'header': {
                    'type': 'string',
                    'value': self._('Document'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render("l['docname']"),
                },
                'totals': {
                    'type': 'string',
                    'value': self._render("p['p_full_name']"),
                },
                'width': 20,
            },
            'sup_inv_nr': {
                'header': {
                    'type': 'string',
                    'value': self._('Supplier Invoice No'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render("l['sup_inv_nr'] or ''"),
                },
                'width': 20,
            },
            'origin': {
                'header': {
                    'type': 'string',
                    'value': self._('Source Document'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render("l['origin'] or ''"),
                },
                'width': 20,
            },
            'date': {
                'header': {
                    'value': self._('Date'),
                },
                'lines': {
                    'value': self._render(
                        "datetime.strptime(l['l_date'], '%Y-%m-%d')"),
                    'format': self.format_tcell_date_left,
                },
                'width': 12,
            },
            'date_maturity': {
                'header': {
                    'value': self._('Due Date'),
                },
                'lines': {
                    'value': self._render(
                        "l['date_due'] and "
                        "datetime.strptime(l['date_due'],'%Y-%m-%d') "
                        "or None"),
                    'format': self.format_tcell_date_left,
                },
                'width': 12,
            },
            'description': {
                'header': {
                    'value': self._('Description'),
                },
                'lines': {
                    'value': self._render("l['l_name']"),
                },
                'width': 60,
            },
            'amount_original': {
                'header': {
                    'value': self._('Original'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l['amount_original']"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("amount_original_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 14,
            },
            'amount_reconciled': {
                'header': {
                    'value': self._('Reconciled'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l['amount_reconciled']"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("amount_reconciled_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 14,
            },
            'balance': {
                'header': {
                    'value': self._('Balance'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'formula',
                    'value': self._render("bal_formula"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("bal_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 14,
            },
            'account': {
                'header': {
                    'value': self._('Account'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render("l['a_code']"),
                    'format': self.format_tcell_center,
                },
                'width': 10,
            },
            'journal': {
                'header': {
                    'value': self._('Journal'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render("l['j_code']"),
                    'format': self.format_tcell_center,
                },
                'width': 10,
            },
            'currency': {
                'header': {
                    'value': self._('Cur.'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render("l['currency'] or ''"),
                    'format': self.format_tcell_center,
                },
                'width': 8,
            },
            'amount_currency': {
                'header': {
                    'value': self._('Cur.Original'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render(
                        "l['currency'] and l['amount_currency']"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 16,
            },
            'amount_currency_reconciled': {
                'header': {
                    'value': self._('Cur.Reconciled'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render(
                        "l['currency'] and l['amount_currency_reconciled']"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 14,
            },
            'rec_details': {
                'header': {
                    'value': self._('Reconcile Details'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render("rec_details"),
                    'format': self.format_tcell_center,
                },
                'width': 16,
            },
            'move_line_id': {
                'header': {
                    'value': self._('Move Line Id'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l['l_id']"),
                    'format': self.format_tcell_integer_right,
                },
                'width': 12,
            },
        }

        return template

    def _details_report(self, workbook, ws, ws_params, data, partners):

        ws.set_landscape()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params)

        ws.freeze_panes(row_pos, 0)

        wiz = ws_params['wiz']
        report = ws_params['report']
        wanted_list = ws_params['wanted_list']
        orig_pos = ('amount_original' in wanted_list
                    and wanted_list.index('amount_original'))
        rec_pos = ('amount_reconciled' in wanted_list
                   and wanted_list.index('amount_reconciled'))

        for partner in report['partners']:

            ws.write_string(row_pos, 0, partner['p_full_name'],
                            self.format_left_bold)
            row_pos += 1
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='header',
                default_format=self.format_theader_yellow_left)

            for line in partner['lines']:
                orig_cell = self._rowcol_to_cell(row_pos, orig_pos)
                rec_cell = self._rowcol_to_cell(row_pos, rec_pos)
                bal_formula = orig_cell + '-' + rec_cell
                render_space = {
                    'l': line,
                    'bal_formula': bal_formula}
                if wiz.add_reconcile:
                    rec_details = ''
                    if line['prl_ids']:
                        rec_details += ','.join(
                            [str(x) for x in line['prl_ids']])
                    if line['fr_name']:
                        rec_details += ' (%s)' % line['fr_name']
                    render_space['rec_details'] = rec_details
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='lines',
                    render_space=render_space,
                    default_format=self.format_tcell_left)
            l_cnt = len(partner['lines'])
            orig_start = self._rowcol_to_cell(row_pos - l_cnt, orig_pos)
            orig_stop = self._rowcol_to_cell(row_pos - 1, orig_pos)
            orig_formula = 'SUM(%s:%s)' % (orig_start, orig_stop)
            rec_start = self._rowcol_to_cell(row_pos - l_cnt, rec_pos)
            rec_stop = self._rowcol_to_cell(row_pos - 1, rec_pos)
            rec_formula = 'SUM(%s:%s)' % (rec_start, rec_stop)
            orig_cell = self._rowcol_to_cell(row_pos, orig_pos)
            rec_cell = self._rowcol_to_cell(row_pos, rec_pos)
            bal_formula = orig_cell + '-' + rec_cell
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='totals',
                render_space={
                    'p': partner,
                    'amount_original_formula': orig_formula,
                    'amount_reconciled_formula': rec_formula,
                    'bal_formula': bal_formula,
                },
                default_format=self.format_theader_yellow_left)
            row_pos += 1
