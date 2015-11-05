# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010-2015 Noviat nv/sa (www.noviat.com).
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
from openerp.osv import orm
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from .account_partner_open_arap import partner_open_arap_print
from openerp.tools.translate import translate
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'account.partner.open.arap'


class partner_open_arap_print_xls(partner_open_arap_print):

    def __init__(self, cr, uid, name, context):
        super(partner_open_arap_print_xls, self).__init__(
            cr, uid, name, context=context)
        p_obj = self.pool['res.partner']
        self.context = context
        wl_ov = p_obj._xls_arap_overview_fields(cr, uid, context)
        tmpl_upd_ov = p_obj._xls_arap_overview_template(cr, uid, context)
        wl_ar_details = p_obj._xls_ar_details_fields(cr, uid, context)
        wl_ap_details = p_obj._xls_ap_details_fields(cr, uid, context)
        tmpl_upd_details = p_obj._xls_arap_details_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list_overview': wl_ov,
            'template_updates_overview': tmpl_upd_ov,
            'wanted_list_ar_details': wl_ar_details,
            'wanted_list_ap_details': wl_ap_details,
            'template_updates_details': tmpl_upd_details,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(
            self.cr, _ir_translation_name, 'report', lang, src) or src


class partner_open_arap_xls(report_xls):

    def __init__(self, name, table, rml=False,
                 parser=False, header=True, store=False):
        super(partner_open_arap_xls, self).__init__(
            name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header

        # Report Column Headers format
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(
            rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])

        # Partner Column Headers format
        fill_blue = 'pattern: pattern solid, fore_color 27;'
        ph_cell_format = _xs['bold'] + fill_blue + _xs['borders_all']
        self.ph_cell_style = xlwt.easyxf(ph_cell_format)
        self.ph_cell_style_decimal = xlwt.easyxf(
            ph_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # Partner Column Data format
        pd_cell_format = _xs['borders_all']
        self.pd_cell_style = xlwt.easyxf(pd_cell_format)
        self.pd_cell_style_center = xlwt.easyxf(
            pd_cell_format + _xs['center'])
        self.pd_cell_style_date = xlwt.easyxf(
            pd_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        self.pd_cell_style_decimal = xlwt.easyxf(
            pd_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(
            rt_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # XLS Template - overview
        self.col_specs_template_overview = {
            'partner': {
                'header': [1, 44, 'text', _render("_('Partner')")],
                'lines': [1, 0, 'text', _render("p['p_name'] or 'n/a'")],
                'totals': [1, 0, 'text', None]},
            'partner_ref': {
                'header': [1, 22, 'text', _render("_('Partner Reference')")],
                'lines': [1, 0, 'text', _render("p['p_ref'] or 'n/a'")],
                'totals': [1, 0, 'text', None]},
            'debit': {
                'header': [
                    1, 14, 'text',
                    _render("_('Debit')"), None, self.rh_cell_style_right],
                'lines': [
                    1, 0, 'number',
                    _render("p['d']"), None, self.pd_cell_style_decimal],
                'totals': [
                    1, 0, 'number', None,
                    _render("debit_formula"), self.rt_cell_style_decimal]},
            'credit': {
                'header': [
                    1, 14, 'text',
                    _render("_('Credit')"), None, self.rh_cell_style_right],
                'lines': [
                    1, 0, 'number',
                    _render("p['c']"), None, self.pd_cell_style_decimal],
                'totals': [
                    1, 0, 'number', None,
                    _render("credit_formula"), self.rt_cell_style_decimal]},
            'balance': {
                'header': [
                    1, 14, 'text',
                    _render("_('Balance')"), None, self.rh_cell_style_right],
                'lines': [
                    1, 0, 'number', None,
                    _render("bal_formula_o"), self.pd_cell_style_decimal],
                'totals': [
                    1, 0, 'number', None,
                    _render("bal_formula"), self.rt_cell_style_decimal]},
        }

        # XLS Template - details - common
        self.col_specs_template_details = {
            'document': {
                'header1': [1, 20, 'text', _render("_('Document')")],
                'header2': [1, 0, 'text', _render("p['p_name'] or 'n/a'")],
                'lines': [1, 0, 'text', _render("l['docname']")],
                'totals1': [1, 0, 'text', None],
                'totals2': [1, 0, 'text', None]},
            'sup_inv_nr': {
                'header1':
                    [1, 20, 'text', _render("_('Supplier Invoice No')")],
                'header2': [1, 0, 'text', None],
                'lines': [1, 0, 'text', _render("l['sup_inv_nr'] or ''")],
                'totals1': [1, 0, 'text', None],
                'totals2': [1, 0, 'text', None]},
            'date': {
                'header1': [1, 12, 'text', _render("_('Date')")],
                'header2': [1, 0, 'text', None],
                'lines': [
                    1, 0, 'date',
                    _render("datetime.strptime(l['l_date'],'%Y-%m-%d')"),
                    None, self.pd_cell_style_date],
                'totals1': [1, 0, 'text', None],
                'totals2': [1, 0, 'text', None]},
            'date_maturity': {
                'header1': [1, 12, 'text', _render("_('Due Date')")],
                'header2': [1, 0, 'text', None],
                'lines': [
                    1, 0, _render("l['date_due'] and 'date' or 'text'"),
                    _render("l['date_due'] and "
                            "datetime.strptime(l['date_due'],'%Y-%m-%d') "
                            "or None"),
                    None, self.pd_cell_style_date],
                'totals1': [1, 0, 'text', None],
                'totals2': [1, 0, 'text', None]},
            'account': {
                'header1': [1, 20, 'text', _render("_('Account')")],
                'header2': [1, 0, 'text', None],
                'lines': [1, 0, 'text', _render("l['a_code']")],
                'totals1': [1, 0, 'text', None],
                'totals2': [1, 0, 'text', None]},
            'description': {
                'header1': [1, 65, 'text', _render("_('Description')")],
                'header2': [1, 42, 'text', _render("p['p_ref'] or 'n/a'")],
                'lines': [1, 0, 'text', _render("l['l_name']")],
                'totals1': [1, 0, 'text', None],
                'totals2': [1, 0, 'text', None]},
            'rec_or_rec_part': {
                'header1': [1, 14, 'text', _render("_('Rec')")],
                'header2': [1, 12, 'text', None],
                'lines': [
                    1, 0, 'text',
                    _render("l['r_name'] or l['rp_name']"), None,
                    self.pd_cell_style_center],
                'totals1': [1, 0, 'text', None],
                'totals2': [
                    1, 14, 'text',
                    _render("_('Totals')"), None,
                    self.rt_cell_style_right]},
            'debit': {
                'header1': [
                    1, 14, 'text',
                    _render("_('Debit')"), None,
                    self.rh_cell_style_right],
                'header2': [
                    1, 0, 'number', None,
                    _render("debit_formula"),
                    self.ph_cell_style_decimal],
                'lines': [
                    1, 0, 'number',
                    _render("l['debit']"), None,
                    self.pd_cell_style_decimal],
                'totals1': [1, 0, 'text', _render("_('Debit')")],
                'totals2': [
                    1, 0, 'number', None,
                    _render("debit_formula"),
                    self.rt_cell_style_decimal]},
            'credit': {
                'header1': [
                    1, 14, 'text',
                    _render("_('Credit')"), None,
                    self.rh_cell_style_right],
                'header2': [
                    1, 0, 'number', None,
                    _render("credit_formula"),
                    self.ph_cell_style_decimal],
                'lines': [
                    1, 0, 'number',
                    _render("l['credit']"), None,
                    self.pd_cell_style_decimal],
                'totals1': [1, 0, 'text', _render("_('Credit')")],
                'totals2': [
                    1, 0, 'number', None,
                    _render("credit_formula"),
                    self.rt_cell_style_decimal]},
            'balance': {
                'header1': [
                    1, 14, 'text',
                    _render("_('Balance')"), None,
                    self.rh_cell_style_right],
                'header2': [
                    1, 18, 'number', None,
                    _render("bal_formula_d"),
                    self.ph_cell_style_decimal],
                'lines': [
                    1, 0, 'number', None,
                    _render("bal_formula"),
                    self.pd_cell_style_decimal],
                'totals1': [1, 0, 'text', _render("_('Balance')")],
                'totals2': [
                    1, 0, 'number', None,
                    _render("bal_formula"),
                    self.rt_cell_style_decimal]},
        }

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        wl_overview = _p.wanted_list_overview
        wl_ar_details = _p.wanted_list_ar_details
        wl_ap_details = _p.wanted_list_ap_details
        self.col_specs_template_overview.update(_p.template_updates_overview)
        self.col_specs_template_details.update(_p.template_updates_details)
        _ = _p._

        # TODO : adapt to allow rendering space extensions by inherited module
        # add objects to the render space for use in custom reports
        partner_obj = self.pool['res.partner']  # noqa: disable F841, report_xls namespace trick

        for i, wl in enumerate([wl_overview, wl_ar_details, wl_ap_details]):
            debit_pos = 'debit' in wl and wl.index('debit')
            credit_pos = 'credit' in wl and wl.index('credit')
            if not (credit_pos and debit_pos) and 'balance' in wl:
                raise orm.except_orm(
                    _('Customisation Error!'),
                    _("The 'Balance' field is a calculated XLS field "
                      "requiring the presence of "
                      "the 'Debit' and 'Credit' fields !"))
            if i == 0:
                debit_pos_o = debit_pos
                credit_pos_o = credit_pos
            elif i == 1:
                debit_pos_ar = debit_pos
                credit_pos_ar = credit_pos
            else:
                debit_pos_ap = debit_pos
                credit_pos_ap = credit_pos

        for r in _p.reports:
            title_short = r['title_short'].replace('/', '-')
            ws_o = wb.add_sheet(title_short)
            ws_d = wb.add_sheet((title_short + ' ' + _('Details'))[:31])
            for ws in [ws_o, ws_d]:
                ws.panes_frozen = True
                ws.remove_splits = True
                ws.portrait = 0  # Landscape
                ws.fit_width_to_pages = 1
            row_pos_o = 0
            row_pos_d = 0
            if r['type'] == 'receivable':
                wanted_list_details = wl_ar_details
                debit_pos_d = debit_pos_ar
                credit_pos_d = credit_pos_ar
            else:
                wanted_list_details = wl_ap_details
                debit_pos_d = debit_pos_ap
                credit_pos_d = credit_pos_ap

            # set print header/footer
            for ws in [ws_o, ws_d]:
                ws.header_str = self.xls_headers['standard']
                ws.footer_str = self.xls_footers['standard']

            # Title
            cell_style = xlwt.easyxf(_xs['xls_title'])
            report_name = '  -  '.join(
                [_p.company.name, r['title'], _('Overview'),
                 _p.report_info + ' - ' + _p.company.currency_id.name])
            c_specs_o = [
                ('report_name', 1, 0, 'text', report_name),
            ]
            row_data = self.xls_row_template(c_specs_o, ['report_name'])
            row_pos_o = self.xls_write_row(
                ws_o, row_pos_o, row_data, row_style=cell_style)
            row_pos_o += 1
            report_name = '  -  '.join(
                [_p.company.name, r['title'], _('Details'),
                 _p.report_info + ' - ' + _p.company.currency_id.name])
            c_specs_d = [
                ('report_name', 1, 0, 'text', report_name),
            ]
            row_data = self.xls_row_template(c_specs_d, ['report_name'])
            row_pos_d = self.xls_write_row(
                ws_d, row_pos_d, row_data, row_style=cell_style)
            row_pos_d += 1

            # Report Column Headers
            c_specs_o = map(
                lambda x: self.render(
                    x, self.col_specs_template_overview, 'header',
                    render_space={'_': _p._}),
                wl_overview)
            row_data = self.xls_row_template(
                c_specs_o, [x[0] for x in c_specs_o])
            row_pos_o = self.xls_write_row(
                ws_o, row_pos_o, row_data, row_style=self.rh_cell_style,
                set_column_size=True)
            ws_o.set_horz_split_pos(row_pos_o)

            c_specs_d = map(
                lambda x: self.render(
                    x, self.col_specs_template_details, 'header1',
                    render_space={'_': _p._}),
                wanted_list_details)
            row_data = self.xls_row_template(
                c_specs_d, [x[0] for x in c_specs_d])
            row_pos_d = self.xls_write_row(
                ws_d, row_pos_d, row_data, row_style=self.rh_cell_style,
                set_column_size=True)
            ws_d.set_horz_split_pos(row_pos_d)
            row_pos_d += 1
            partner_debit_cells = []
            partner_credit_cells = []

            for p in r['partners']:

                debit_cell_o = rowcol_to_cell(row_pos_o, debit_pos_o)
                credit_cell_o = rowcol_to_cell(row_pos_o, credit_pos_o)
                bal_formula_o = debit_cell_o + '-' + credit_cell_o  # noqa: disable F841, report_xls namespace trick
                c_specs_o = map(
                    lambda x: self.render(
                        x, self.col_specs_template_overview, 'lines'),
                    wl_overview)
                row_data = self.xls_row_template(
                    c_specs_o, [x[0] for x in c_specs_o])
                row_pos_o = self.xls_write_row(
                    ws_o, row_pos_o, row_data, row_style=self.pd_cell_style)

                row_pos_d += 1

                debit_cell_d = rowcol_to_cell(row_pos_d, debit_pos_d)
                credit_cell_d = rowcol_to_cell(row_pos_d, credit_pos_d)
                partner_debit_cells.append(debit_cell_d)
                partner_credit_cells.append(credit_cell_d)

                bal_formula_d = debit_cell_d + '-' + credit_cell_d  # noqa: disable F841, report_xls namespace trick

                line_cnt = len(p['lines'])
                debit_start = rowcol_to_cell(row_pos_d+1, debit_pos_d)
                debit_stop = rowcol_to_cell(row_pos_d+line_cnt, debit_pos_d)
                debit_formula = 'SUM(%s:%s)' % (debit_start, debit_stop)
                credit_start = rowcol_to_cell(row_pos_d+1, credit_pos_d)
                credit_stop = rowcol_to_cell(row_pos_d+line_cnt, credit_pos_d)
                credit_formula = 'SUM(%s:%s)' % (credit_start, credit_stop)
                c_specs_d = map(
                    lambda x: self.render(
                        x, self.col_specs_template_details, 'header2'),
                    wanted_list_details)
                row_data = self.xls_row_template(
                    c_specs_d, [x[0] for x in c_specs_d])
                row_pos_d = self.xls_write_row(
                    ws_d, row_pos_d, row_data, row_style=self.ph_cell_style)

                for l in p['lines']:

                    debit_cell = rowcol_to_cell(row_pos_d, debit_pos_d)
                    credit_cell = rowcol_to_cell(row_pos_d, credit_pos_d)
                    bal_formula = debit_cell + '-' + credit_cell
                    c_specs_d = map(
                        lambda x: self.render(
                            x, self.col_specs_template_details, 'lines'),
                        wanted_list_details)
                    row_data = self.xls_row_template(
                        c_specs_d, [x[0] for x in c_specs_d])
                    row_pos_d = self.xls_write_row(
                        ws_d, row_pos_d, row_data,
                        row_style=self.pd_cell_style)

            # Totals
            p_cnt = len(r['partners'])
            debit_start = rowcol_to_cell(row_pos_o - p_cnt, debit_pos_o)
            debit_stop = rowcol_to_cell(row_pos_o - 1, debit_pos_o)
            debit_formula = 'SUM(%s:%s)' % (debit_start, debit_stop)
            credit_start = rowcol_to_cell(row_pos_o - p_cnt, credit_pos_o)
            credit_stop = rowcol_to_cell(row_pos_o - 1, credit_pos_o)
            credit_formula = 'SUM(%s:%s)' % (credit_start, credit_stop)
            debit_cell = rowcol_to_cell(row_pos_o, debit_pos_o)
            credit_cell = rowcol_to_cell(row_pos_o, credit_pos_o)
            bal_formula = debit_cell + '-' + credit_cell
            c_specs_o = map(
                lambda x: self.render(
                    x, self.col_specs_template_overview, 'totals'),
                wl_overview)
            row_data = self.xls_row_template(
                c_specs_o, [x[0] for x in c_specs_o])
            row_pos_o = self.xls_write_row(
                ws_o, row_pos_o, row_data, row_style=self.rt_cell_style_right)

            row_pos_d += 1
            c_specs_d = map(
                lambda x: self.render(
                    x, self.col_specs_template_details, 'totals1',
                    render_space={'_': _p._}),
                wanted_list_details)
            row_data = self.xls_row_template(
                c_specs_d, [x[0] for x in c_specs_d])
            row_pos_d = self.xls_write_row(
                ws_d, row_pos_d, row_data, row_style=self.rt_cell_style_right)

            debit_cell = rowcol_to_cell(row_pos_d, debit_pos_d)
            credit_cell = rowcol_to_cell(row_pos_d, credit_pos_d)
            bal_formula = debit_cell + '-' + credit_cell  # noqa: disable F841, report_xls namespace trick
            debit_formula = '+'.join(partner_debit_cells)  # noqa: disable F841, report_xls namespace trick
            credit_formula = '+'.join(partner_credit_cells)  # noqa: disable F841, report_xls namespace trick
            c_specs_d = map(
                lambda x: self.render(
                    x, self.col_specs_template_details, 'totals2'),
                wanted_list_details)
            row_data = self.xls_row_template(
                c_specs_d, [x[0] for x in c_specs_d])
            row_pos_d = self.xls_write_row(
                ws_d, row_pos_d, row_data, row_style=self.rt_cell_style_right)

    # end def generate_xls_report

# end class partner_open_arap_xls

partner_open_arap_xls(
    'report.account.partner.open.arap.period.xls',
    'account.period',
    parser=partner_open_arap_print_xls)
