# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
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

import xlwt
from datetime import datetime
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.tools.translate import translate

_ir_translation_name = 'invoice.line.xls'


class invoice_line_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(invoice_line_xls_parser, self).__init__(
            cr, uid, name, context=context)
        inv_line_obj = self.pool.get('account.invoice.line')
        self.context = context
        wanted_list = inv_line_obj._report_xls_fields(cr, uid, context)
        template_changes = inv_line_obj._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
            'template_changes': template_changes,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) \
            or src


class invoice_line_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(invoice_line_xls, self).__init__(
            name, table, rml=rml, parser=parser, header=header, store=store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(
            rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(
            rh_cell_format + _xs['right'])
        # lines
        ail_cell_format = _xs['borders_all']
        self.ail_cell_style = xlwt.easyxf(ail_cell_format)
        self.ail_cell_style_center = xlwt.easyxf(
            ail_cell_format + _xs['center'])
        self.ail_cell_style_date = xlwt.easyxf(
            ail_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        self.ail_cell_style_decimal = xlwt.easyxf(
            ail_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(
            rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(
            rt_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # XLS Template
        self.col_specs_template = {
            'invoice_number': {
                'header': [1, 16, 'text', _render("_('Invoice Number')")],
                'lines': [1, 0, 'text', _render("line.invoice_number or ''")],
                'totals': [1, 0, 'text', None]},
            'invoice_type': {
                'header': [1, 13, 'text', _render("_('Invoice Type')")],
                'lines': [1, 0, 'text', _render("line.invoice_type or ''")],
                'totals': [1, 0, 'text', None]},
            'invoice_state': {
                'header': [1, 13, 'text', _render("_('Invoice State')")],
                'lines': [1, 0, 'text', _render("line.invoice_state or ''")],
                'totals': [1, 0, 'text', None]},
            'journal': {
                'header': [1, 9, 'text', _render("_('Journal')")],
                'lines': [1, 0, 'text',
                          _render("line.invoice_journal_id.code or ''")],
                'totals': [1, 0, 'text', None]},
            'partner': {
                'header': [1, 36, 'text', _render("_('Partner')")],
                'lines': [1, 0, 'text',
                          _render("line.invoice_partner_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'partner_ref': {
                'header': [1, 36, 'text', _render("_('Partner Reference')")],
                'lines':
                    [1, 0, 'text',
                     _render("line.partner_id and line.partner_id.ref or ''")
                     ],
                'totals': [1, 0, 'text', None]},
            'date': {
                'header': [1, 14, 'text', _render("_('Invoice Date')")],
                'lines':
                    [1, 0, 'date', _render(
                        "datetime.strptime(line.invoice_date,'%Y-%m-%d')"),
                     None, self.ail_cell_style_date],
                'totals': [1, 0, 'text', None]},
            'account': {
                'header': [1, 13, 'text', _render("_('Account')")],
                'lines': [1, 0, 'text', _render("line.account_id.code")],
                'totals': [1, 0, 'text', None]},
            'description': {
                'header': [1, 40, 'text', _render("_('Description')")],
                'lines': [1, 0, 'text',
                          _render("line.name and line.name or ''")],
                'totals': [1, 0, 'text', None]},
            'product': {
                'header': [1, 40, 'text', _render("_('Product')")],
                'lines': [1, 0, 'text',
                          _render("line.product_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'product_ref': {
                'header': [1, 36, 'text', _render("_('Product Reference')")],
                'lines': [1, 0, 'text',
                          _render("line.product_id.default_code or ''")],
                'totals': [1, 0, 'text', None]},
            'product_uos': {
                'header': [1, 10, 'text', _render("_('Unit of Sale')")],
                'lines': [1, 0, 'text', _render("line.uos_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'quantity': {
                'header':
                    [1, 8, 'text',
                     _render("_('Qty')"), None, self.rh_cell_style_right],
                'lines': [
                    1, 0, 'number',
                    _render("line.quantity"),
                    None, self.ail_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'price_unit': {
                'header':
                    [1, 18, 'text',
                     _render("_('Unit Price')"),
                     None, self.rh_cell_style_right],
                'lines':
                    [1, 0, 'number',
                     _render("line.price_unit"),
                     None, self.ail_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'discount': {
                'header':
                    [1, 12, 'text',
                     _render("_('Discount' + ' (%)')"),
                     None, self.rh_cell_style_right],
                'lines':
                    [1, 0, 'number',
                     _render("line.discount"),
                     None, self.ail_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'price_subtotal': {
                'header':
                    [1, 18, 'text',
                     _render("_('Subtotal')"),
                     None, self.rh_cell_style_right],
                'lines':
                    [1, 0, 'number',
                     _render("line.price_subtotal"),
                     None, self.ail_cell_style_decimal],
                'totals':
                    [1, 0, 'number',
                     None, _render("subtotal_formula"),
                     self.rt_cell_style_decimal]},
            'analytic_account': {
                'header': [1, 40, 'text', _render("_('Analytic Account')")],
                'lines':
                    [1, 0, 'text',
                     _render("line.account_analytic_id.code or ''")],
                'totals': [1, 0, 'text', None]},
            'note': {
                'header': [1, 42, 'text', _render("_('Notes')")],
                'lines': [1, 0, 'text', _render("line.note or ''")],
                'totals': [1, 0, 'text', None]},
        }

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        wanted_list = _p.wanted_list
        self.col_specs_template.update(_p.template_changes)
        _ = _p._

        subtotal_pos = 'price_subtotal' in wanted_list \
            and wanted_list.index('price_subtotal')
        report_name = _("Invoice Lines")
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
        c_specs = map(
            lambda x: self.render(
                x, self.col_specs_template, 'header',
                render_space={'_': _p._}),
            wanted_list)
        row_data = self.xls_row_template(
            c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style,
            set_column_size=True)
        ws.set_horz_split_pos(row_pos)
        ws.set_vert_split_pos(1)

        # invoice lines
        for line in objects:
            c_specs = map(
                lambda x: self.render(
                    x, self.col_specs_template, 'lines'),
                wanted_list)
            row_data = self.xls_row_template(
                c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.ail_cell_style)

        # Totals
        ail_cnt = len(objects)
        if subtotal_pos:
            subtotal_start = rowcol_to_cell(row_pos - ail_cnt, subtotal_pos)
            subtotal_stop = rowcol_to_cell(row_pos - 1, subtotal_pos)
            subtotal_formula = 'SUM(%s:%s)' % (subtotal_start, subtotal_stop)  # noqa: disable F841, report_xls namespace trick
        c_specs = map(
            lambda x: self.render(
                x, self.col_specs_template, 'totals'),
            wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rt_cell_style_right)

invoice_line_xls(
    'report.invoice.line.xls',
    'account.invoice.line',
    parser=invoice_line_xls_parser)
