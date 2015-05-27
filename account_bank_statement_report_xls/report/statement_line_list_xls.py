# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013-2015 Noviat nv/sa (www.noviat.com).
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

import xlwt
from datetime import datetime
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class statement_line_xls(report_xls):

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        report_name = _('Bank Statement Lines')
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)
        row_pos += 1

        # Column headers
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        rh_cell_style = xlwt.easyxf(rh_cell_format)
        # rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        c_specs = [
            ('j_code', 1, 10, 'text', _('Journal')),
            ('date', 1, 13, 'text', _('Date')),
            ('statement', 1, 15, 'text',  _('Statement')),
            ('partner', 1, 36, 'text',  _('Partner')),
            ('communication', 1, 40, 'text', _('Communication')),
            ('amount', 1, 18, 'text',  _('Amount'), None, rh_cell_style_right),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=rh_cell_style,
            set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        # statement lines
        absl_cell_format = _xs['borders_all']
        absl_cell_style = xlwt.easyxf(absl_cell_format)
        # absl_cell_style_center = xlwt.easyxf(
        #    absl_cell_format + _xs['center'])
        absl_cell_style_date = xlwt.easyxf(
            absl_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        absl_cell_style_decimal = xlwt.easyxf(
            absl_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        for line in objects:
            absl_date = line.val_date or line.date
            c_specs = [
                ('j_code', 1, 0, 'text', line.statement_id.journal_id.code),
                ('val_date', 1, 0, 'date',
                 datetime.strptime(absl_date, '%Y-%m-%d'),
                 None, absl_cell_style_date),
                ('statement', 1, 0, 'text', line.statement_id.name),
                ('partner', 1, 0, 'text',
                 line.partner_id and line.partner_id.name or ''),
                ('communication', 1, 0, 'text', line.name),
                ('amount', 1, 0, 'number', line.amount,
                 None, absl_cell_style_decimal),
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=absl_cell_style)

        # Total
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        # rt_cell_style = xlwt.easyxf(rt_cell_format)
        rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        rt_cell_style_decimal = xlwt.easyxf(
            rt_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        absl_cnt = len(objects)
        amount_start = rowcol_to_cell(row_pos - absl_cnt, 5)
        amount_stop = rowcol_to_cell(row_pos - 1, 5)
        total_formula = 'SUM(%s:%s)' % (amount_start, amount_stop)

        c_specs = [('empty%s' % i, 1, 0, 'text', None) for i in range(0, 5)]
        c_specs += [
            ('total', 1, 0, 'number', None,
             total_formula, rt_cell_style_decimal),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=rt_cell_style_right)


statement_line_xls(
    'report.statement.line.list.xls',
    'account.bank.statement.line',
    parser=report_sxw.rml_parse)
