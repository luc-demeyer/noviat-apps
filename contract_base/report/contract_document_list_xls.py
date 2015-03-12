# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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

from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.tools.translate import _
import xlwt
import time
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class contract_document_xls(report_xls):

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        report_name = 'Contract Overview'
        ws = wb.add_sheet(report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
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
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
        row_pos += 1

        # Column headers
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        rh_cell_style = xlwt.easyxf(rh_cell_format)
        rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])  
        c_specs = [
            ('name', 1, 30, 'text', _('Reference')),
            ('date_start', 1, 13, 'text', _('Date Start')),
            ('partner', 1, 35, 'text',  _('Partner')),
            ('category', 1, 15, 'text',  _('Category')),
            ('total_mrc', 1, 18, 'text',  _('Total MRC'), None, rh_cell_style_right),
            ('total_otc', 1, 18, 'text',  _('Total OTC'), None, rh_cell_style_right),
            ('currency', 1, 10, 'text',  _('Curr.'), None, rh_cell_style_center),
            ('state', 1, 10, 'text',  _('State'), None, rh_cell_style_center),
            ('type', 1, 10, 'text',  _('Type'), None, rh_cell_style_center),
            ('uid', 1, 20, 'text',  _('Contract Owner')),
            ('analytic', 1, 30, 'text',  _('Analytic account')),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=rh_cell_style, set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        # data
        o_cell_format = _xs['borders_all']
        o_cell_style = xlwt.easyxf(o_cell_format)
        o_cell_style_center = xlwt.easyxf(o_cell_format + _xs['center'])
        o_cell_style_date = xlwt.easyxf(o_cell_format + _xs['left'], num_format_str = report_xls.date_format)
        o_cell_style_decimal = xlwt.easyxf(o_cell_format + _xs['right'], num_format_str = report_xls.decimal_format)
        for o in objects:
            c_specs = [
                ('name', 1, 0, 'text', o.name),
                ('date_start', 1, 0, 'date', datetime.strptime(o.date_start,'%Y-%m-%d'), None, o_cell_style_date),
                ('partner', 1, 0, 'text', o.partner_id.name),
                ('category', 1, 0, 'text', o.categ_id.code or ''),
                ('total_mrc', 1, 0, 'number', o.total_mrc, None, o_cell_style_decimal),
                ('total_otc', 1, 0, 'number', o.total_otc, None, o_cell_style_decimal),
                ('currency', 1, 0, 'text', o.currency_id.name, None, o_cell_style_center),
                ('state', 1, 0, 'text', o.state, None, o_cell_style_center),
                ('type', 1, 0, 'text', o.type, None, o_cell_style_center),
                ('uid', 1, 0, 'text', o.user_id.name),
                ('analytic', 1, 0, 'text', o.analytic_account_id and o.analytic_account_id.name or ''),
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=o_cell_style)

        # Totals           
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        rt_cell_style = xlwt.easyxf(rt_cell_format)
        rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])       
        rt_cell_style_decimal = xlwt.easyxf(rt_cell_format + _xs['right'], num_format_str = report_xls.decimal_format)

        o_cnt = len(objects)
        mrc_start = rowcol_to_cell(row_pos - o_cnt, 4)
        mrc_stop = rowcol_to_cell(row_pos - 1, 4)
        mrc_formula = 'SUM(%s:%s)' %(mrc_start, mrc_stop)
        otc_start = rowcol_to_cell(row_pos - o_cnt, 5)
        otc_stop = rowcol_to_cell(row_pos - 1,  5)
        otc_formula = 'SUM(%s:%s)' %(otc_start, otc_stop)

        c_specs = [('empty%s'%i, 1, 0, 'text', None) for i in range(0,4)] 
        c_specs += [
            ('total_mrc', 1, 0, 'number', None, mrc_formula, rt_cell_style_decimal),
            ('total_otc', 1, 0, 'number', None, otc_formula, rt_cell_style_decimal),
        ]       
        c_specs += [('empty%s'%i, 1, 0, 'text', None) for i in range(7,12)] 
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=rt_cell_style_right) 

contract_document_xls('report.contract.document.list.xls', 
    'contract.document',
    parser=report_sxw.rml_parse)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: