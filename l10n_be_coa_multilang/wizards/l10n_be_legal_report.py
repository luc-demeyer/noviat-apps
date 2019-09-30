# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.tools.translate import translate

_logger = logging.getLogger(__name__)

IR_TRANSLATION_NAME = 'l10n.be.legal.report'


class l10nBeLegalReport(models.TransientModel):
    _name = 'l10n.be.legal.report'
    _inherit = 'l10n.be.vat.common'
    _description = 'Belgium Balance Sheet and P&L (Full Model)'

    chart_id = fields.Many2one(
        comodel_name='be.legal.financial.report.chart',
        required=True,
        domain=[('parent_id', '=', False)],
        string='Report')
    type = fields.Selection(
        selection=[('bs', 'Balance Sheet'),
                   ('pl', 'Profit & Loss')])
    target_move = fields.Selection(
        selection=[('posted', 'All Posted Entries'),
                   ('all', 'All Entries')],
        string='Target Moves', default='posted', required=True)
    line_ids = fields.One2many(
        comodel_name='l10n.be.legal.report.line',
        inverse_name='report_id',
        string='Report Entries')
    date_to = fields.Date(required=True)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        super()._onchange_company_id()
        if self.company_id:
            dates = self.company_id.compute_fiscalyear_dates(
                fields.Date.today())
            self.date_from = dates['date_from']
            self.date_to = dates['date_to']

    @api.onchange('chart_id')
    def _onchange_chart_id(self):
        bs = self.env.ref('l10n_be_coa_multilang.be_report_chart_BE_3_FULL')
        if not self.chart_id:
            self.type = False
        elif self.chart_id == bs:
            self.type = 'bs'
        else:
            self.type = 'pl'

    @api.multi
    def generate_report(self):
        self.ensure_one()
        self._be_scheme_entries = self.env[
            'be.legal.financial.report.scheme'].search([])
        self._accounts = self.env['account.account'].search(
            [('company_id', '=', self.company_id.id)])
        line_vals = self._get_line_vals()
        self.line_ids = [(0, 0, x) for x in line_vals]
        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.%s_view_form_report' % (module, self._table))
        return {
            'name': self.chart_id.name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'target': 'inline',
            'view_id': result_view.id,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def create_xls(self):
        report_file = '{}-{}'.format(self.type, self.date_to)
        module = __name__.split('addons.')[1].split('.')[0]
        report_name = '{}.legal_report_xls'.format(module)
        report = {
            'name': self.chart_id.name,
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': report_name,
            'report_file': report_name,
            'context': dict(self.env.context, report_file=report_file),
            'data': {'dynamic_report': True},
        }
        return report

    @api.multi
    def print_report(self):
        module = __name__.split('addons.')[1].split('.')[0]
        return self.env.ref(
            '%s.action_report_l10nbelegalreport' % module
            ).report_action(self)

    def _get_move_line_date_domain(self):
        date_dom = [
            ('company_id', '=', self.company_id.id),
            ('date', '<=', self.date_to)]
        if self.target_move == 'posted':
            date_dom.append(('move_id.state', '=', 'posted'))
        if self.type == 'pl':
            date_dom.append(('date', '>=', self.date_from))
        return date_dom

    def _get_chart_entry_domain(self, chart_entry):
        if not hasattr(self, '_be_scheme_entries'):
            self._be_scheme_entries = self.env[
                'be.legal.financial.report.scheme'].search([])
        if not hasattr(self, '_accounts'):
            self._accounts = self.env['account.account'].search(
                [('company_id', '=', self.company_id.id)])
        chart_schemes = self._be_scheme_entries.filtered(
            lambda r: r.report_chart_id == chart_entry)
        account_groups = chart_schemes.mapped('account_group')

        def account_groups_filter(account):
            for account_group in account_groups:
                if account_group == account.code[0:len(account_group)]:
                    return True
            return False

        accounts = self._accounts.filtered(account_groups_filter)
        return [('account_id', 'in', accounts.ids)]

    def _calc_parent_chart_amounts(self, chart, amounts):
        if chart.id not in amounts:
            for child in chart.child_ids:
                if child.id not in amounts:
                    self._calc_parent_chart_amounts(child, amounts)
            amounts[chart.id] = sum(
                [x.factor * amounts[x.id] for x in chart.child_ids])

    def _get_line_amounts(self, chart_root):
        chart_entries = chart_root.search(
            [('parent_id', 'child_of', chart_root.id),
             ('child_ids', '=', False)])

        amounts = {}
        date_dom = self._get_move_line_date_domain()
        for chart_entry in chart_entries:
            aml_dom = date_dom + self._get_chart_entry_domain(chart_entry)
            flds = ['balance']
            groupby = []
            amt = self.env['account.move.line'].read_group(
                aml_dom, flds, groupby)[0]
            amounts[chart_entry.id] = self.currency_id.round(
                chart_entry.balance_factor * (amt['balance'] or 0.0))

        self._calc_parent_chart_amounts(chart_root, amounts)

        return amounts

    def _get_chart_child(self, chart, level, line_vals, line_amounts):
        line_vals.append({
            'chart_id': chart.id,
            'level': level,
            'active': not chart.invisible,
            'amount': line_amounts.get(chart.id, 0.0),
        })
        for child in chart.child_ids:
            self._get_chart_child(child, level + 1, line_vals, line_amounts)

    def _get_line_vals(self):
        line_amounts = self._get_line_amounts(self.chart_id)
        line_vals = []
        level = 0
        for child in self.chart_id.child_ids:
            self._get_chart_child(child, level, line_vals, line_amounts)
        return line_vals


class l10nBeLegalReportLine(models.TransientModel):
    _name = 'l10n.be.legal.report.line'
    _order = 'sequence'
    _description = 'Legal report lines'

    report_id = fields.Many2one(
        comodel_name='l10n.be.legal.report',
        string='Report')
    chart_id = fields.Many2one(
        comodel_name='be.legal.financial.report.chart',
        string='Code')
    code = fields.Char(related='chart_id.code')
    amount = fields.Monetary(
        currency_field='currency_id')
    sequence = fields.Integer(
        related='chart_id.sequence', store=True)
    level = fields.Integer()
    active = fields.Boolean()
    color = fields.Char(
        related='chart_id.color')
    font = fields.Selection(
        related='chart_id.font')
    currency_id = fields.Many2one(
        related='report_id.currency_id')

    @api.multi
    def view_move_lines(self):
        self.ensure_one()
        act_window = self.report_id._move_lines_act_window()
        date_dom = self.report_id._get_move_line_date_domain()
        if self.chart_id.child_ids:
            chart_dom = []
            charts = self.chart_id.search(
                [('parent_id', 'child_of', self.chart_id.id),
                 ('child_ids', '=', False)])
            for i, chart in enumerate(charts, start=1):
                if i != len(charts):
                    chart_dom += ['|']
                chart_dom += self.report_id._get_chart_entry_domain(chart)
        else:
            chart_dom = self.report_id._get_chart_entry_domain(self.chart_id)
        act_window['domain'] = date_dom + chart_dom
        return act_window


class l10nBeLegalReportXlsx(models.AbstractModel):
    _name = 'report.l10n_be_coa_multilang.legal_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, workbook, data, be_report):

        col_specs = {
            'code': {
                'header': {
                    'value': self._('Code'),
                },
                'lines': {
                    'value': self._render("l.chart_id.code"),
                },
                'width': 8,
            },
            'name': {
                'header': {
                    'value': self._('Description'),
                },
                'lines': {
                    'value': self._render("l.chart_id.name"),
                },
                'width': 70,
            },
            'amount': {
                'header': {
                    'value': self._('Amount'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l.amount"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
        }
        wanted_list = ['code', 'name', 'amount']

        return [{
            'ws_name': '{}-{}'.format(be_report.type, be_report.date_to),
            'generate_ws_method': '_generate_be_report',
            'title': be_report.chart_id.name,
            'wanted_list': wanted_list,
            'col_specs': col_specs,
        }]

    def _generate_be_report(self, workbook, ws, ws_params, data,
                            be_report):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._be_report_title(ws, row_pos, ws_params, data,
                                        be_report)
        row_pos = self._be_report_info(ws, row_pos, ws_params, data,
                                       be_report)
        row_pos = self._be_report_lines(ws, row_pos, ws_params, data,
                                        be_report)

    def _be_report_title(self, ws, row_pos, ws_params, data, be_report):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _be_report_info(self, ws, row_pos, ws_params, data, be_report):
        ws.write_string(row_pos, 1, self._('Company') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, be_report.company_id.name)
        row_pos += 1
        ws.write_string(row_pos, 1, self._('VAT Number') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, be_report.company_id.vat or '')
        row_pos += 1

        if be_report.type == 'pl':
            ws.write_string(row_pos, 1, self._('Start Date') + ':',
                            self.format_left_bold)
            date_from = fields.Date.to_string(be_report.date_from)
            ws.write_string(row_pos, 2, date_from)
            row_pos += 1
        ws.write_string(row_pos, 1, self._('End Date') + ':',
                        self.format_left_bold)
        date_to = fields.Date.to_string(be_report.date_to)
        ws.write_string(row_pos, 2, date_to)
        return row_pos + 2

    def _be_report_lines(self, ws, row_pos, ws_params, data, be_report):

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        for l in be_report.line_ids:
            if not l.code:
                continue
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={'l': l},
                default_format=self.format_tcell_left)

        return row_pos + 1
