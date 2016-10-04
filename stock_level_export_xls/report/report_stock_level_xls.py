# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
import logging
import xlwt

from openerp import api, fields
from openerp.exceptions import Warning as UserError
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.tools.translate import translate

_ir_translation_name = 'stock.level.xls'
_logger = logging.getLogger(__name__)


class StockLevelXlsParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(StockLevelXlsParser, self).__init__(
            cr, uid, name, context=context)
        self.env = api.Environment(cr, uid, context)
        product_obj = self.pool['product.product']
        self.context = context
        wanted_list = product_obj._stock_level_export_xls_fields(
            cr, uid, context=context)
        template_changes = product_obj.stock_level_export_xls_template(
            cr, uid, context=context)
        self.localcontext.update({
            'wanted_list': wanted_list,
            'template_changes': template_changes,
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(
            self.cr, _ir_translation_name, 'report', lang, src) or src


class StockLevelXls(report_xls):

    def __init__(self, name, table, rml=False, parser=False,
                 header=True, store=False, register=True):
        super(StockLevelXls, self).__init__(
            name, table, rml=rml, parser=parser,
            header=header, store=store, register=register)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # products
        p_cell_format = _xs['borders_all']
        self.p_cell_style = xlwt.easyxf(p_cell_format)
        self.p_cell_style_center = xlwt.easyxf(p_cell_format + _xs['center'])
        self.p_cell_style_date = xlwt.easyxf(
            p_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        self.p_cell_style_decimal = xlwt.easyxf(
            p_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(
            rt_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # XLS Template
        self.col_specs_template = {
            'location': {
                'header': [1, 42, 'text', _render("_('Stock Location')")],
                'products': [
                    1, 0, 'text',
                    _render("product.location "
                            "and product.location.complete_name "
                            "or ''")],
                'totals': [1, 0, 'text', None]},
            'ref': {
                'header': [1, 42, 'text', _render("_('Product Reference')")],
                'products': [1, 0, 'text',
                             _render("product.default_code or ''")],
                'totals': [1, 0, 'text', None]},
            'name': {
                'header': [1, 42, 'text', _render("_('Product Name')")],
                'products': [1, 0, 'text', _render("product.name or ''")],
                'totals': [1, 0, 'text', None]},
            'category': {
                'header': [1, 42, 'text', _render("_('Product Category')")],
                'products': [1, 0, 'text',
                             _render("product.categ_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'uom': {
                'header': [1, 18, 'text', _render("_('Product UOM')")],
                'products': [
                    1, 0, 'text',
                    _render("product.uom_id and product.uom_id.name or ''")],
                'totals': [1, 0, 'text', None]},
            'quantity': {
                'header': [1, 18, 'text',
                           _render("_('Quantity')"),
                           None, self.rh_cell_style_right],
                'products': [
                    1, 0, 'number', _render(
                        "(product.qty_available_at_date) "
                        "or ''"),
                    None, self.p_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'cost': {
                'header': [1, 18, 'text', _render("_('Cost')"),
                           None, self.rh_cell_style_right],
                'products': [1, 0, 'number',
                             _render("product.cost_at_date or ''"),
                             None, self.p_cell_style_decimal],
                'totals': [1, 0, 'text', None]},
            'stock_value': {
                'header': [1, 18, 'text',
                           _render("_('Stock Value')"),
                           None, self.rh_cell_style_right],
                'products': [1, 0, 'number', None,
                             _render("stock_value_formula"),
                             self.p_cell_style_decimal],
                'totals': [1, 0, 'number', None,
                           _render("total_value_formula"),
                           self.rt_cell_style_decimal]},
            'location_id': {
                'header': [1, 13, 'text', 'location_id',
                           None, self.rh_cell_style_right],
                'products': [1, 0, 'number', _render("product.location.id")],
                'totals': [1, 0, 'text', None]},
            'product_id': {
                'header': [1, 13, 'text', 'product_id',
                           None, self.rh_cell_style_right],
                'products': [1, 0, 'number', _render("product.id")],
                'totals': [1, 0, 'text', None]},
            'product_uom_id': {
                'header': [1, 13, 'text', 'product_uom_id',
                           None, self.rh_cell_style_right],
                'products': [
                    1, 0, 'number',
                    _render("product.uom_id and product.uom_id.id or ''")],
                'totals': [1, 0, 'text', None]},
        }

    def _get_stock_data(self, data, warehouse):
        ctx = self.context.copy()
        ctx['force_company'] = data['company_id']
        if warehouse:
            ctx['warehouse'] = warehouse.id
        if data['stock_level_date']:
            ctx['to_date'] = data['stock_level_date']
        product_lines = []
        if data.get('location_ids'):
            for location_id in data['location_ids']:
                location = self.env['stock.location'].browse(location_id)
                products = self.env['product.product'].with_context(
                    dict(ctx, location=location_id)).browse(
                    data['product_ids'])
                for product in products:
                    product.location = location
                    product_lines.append(product)
        else:
            products = self.env['product.product'].with_context(ctx).browse(
                data['product_ids'])
            for product in products:
                product.location = False
                product_lines.append(product)
        extras = products._compute_cost_and_qty_available_at_date()
        report_lines = []
        for product in product_lines:
            qty, cost = extras[product.id]
            if not qty and not data['import_compatible']:
                # Drop empty lines if output is a stock valuation report.
                # Keep those lines if output is intended for
                # import with new inventory values.
                continue
            product.qty_available_at_date = qty
            product.cost_at_date = cost
            report_lines.append(product)
        return report_lines

    def _warehouse_report(self, _p, _xs, data, wb, warehouse):
        product_lines = self._get_stock_data(data, warehouse)
        if warehouse and not product_lines and len(data['warehouse_ids']) > 1:
            return

        wanted_list = _p.wanted_list
        if data['import_compatible']:
            for x in ['location', 'location_id', 'product_id', 'product_uom_id']:
                if x not in wanted_list:
                    wanted_list.append(x)
        _ = _p._

        cost_pos = 'cost' in wanted_list and wanted_list.index('cost')
        quantity_pos = 'quantity' in wanted_list \
            and wanted_list.index('quantity')
        stock_value_pos = 'stock_value' in wanted_list \
            and wanted_list.index('stock_value')
        if not (cost_pos and quantity_pos) and 'stock_value' in wanted_list:
            raise UserError(
                _("Customization Error !"),
                _("The 'Stock Value' field is a calculated XLS field "
                  "requiring the presence of "
                  "the 'Cost' and 'Quantity' fields!"))

        if warehouse:
            sheet_name = warehouse.name
            report_name = _("Warehouse") + ' ' + sheet_name + ' - '
        else:
            sheet_name = _("All Warehouses")
            report_name = sheet_name + ' - '
        stock_level_date = data['stock_level_date'] or fields.Datetime.now()
        stock_level_date_dt = datetime.strptime(
            stock_level_date, '%Y-%m-%d %H:%M:%S')
        stock_level_date_dt = fields.Datetime.context_timestamp(
            warehouse, stock_level_date_dt)
        stock_level_date_dt_fmt = datetime.strftime(
            stock_level_date_dt, '%Y-%m-%d %H:%M:%S')
        report_name += _("Stock Levels at %s") % stock_level_date_dt_fmt
        ws = wb.add_sheet(sheet_name[:31])
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

        # Filters
        filter = False
        if data.get('category_id'):
            filter = True
            category = self.env['product.category'].browse(
                data['category_id'])
            c_specs = [
                ('category', 1, 0, 'text',
                 _("Product Category") + ': ' + category.name),
            ]
            row_data = self.xls_row_template(c_specs, ['category'])
            row_pos = self.xls_write_row(ws, row_pos, row_data)
        if data['product_select'] == 'select':
            filter = True
            c_specs = [
                ('product_select', 1, 0, 'text',
                 _("Products") + ': ' + _("Selected Products")),
            ]
            row_data = self.xls_row_template(c_specs, ['product_select'])
            row_pos = self.xls_write_row(ws, row_pos, row_data)
        if filter:
            row_pos += 1

        if not product_lines:
            c_specs = [
                ('nodata', 1, 0, 'text',
                 _("No product records with stock found "
                   "for your selection.")),
            ]
            row_data = self.xls_row_template(c_specs, ['nodata'])
            row_pos = self.xls_write_row(ws, row_pos, row_data)
            return

        # Column headers
        c_specs = map(
            lambda x: self.render(
                x, self.col_specs_template, 'header',
                render_space={'_': _p._}), wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style,
            set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        # Product lines
        for product in product_lines:
            cost_cell = rowcol_to_cell(row_pos, cost_pos)
            quantity_cell = rowcol_to_cell(row_pos, quantity_pos)
            stock_value_formula = cost_cell + '*' + quantity_cell  # noqa: disable F841, report_xls namespace trick

            c_specs = map(
                lambda x: self.render(
                    x, self.col_specs_template, 'products'), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.p_cell_style)

        # Totals
        line_cnt = len(product_lines)
        stock_value_start = rowcol_to_cell(
            row_pos - line_cnt, stock_value_pos)
        stock_value_stop = rowcol_to_cell(row_pos - 1, stock_value_pos)
        total_value_formula = 'SUM(%s:%s)' % (  # noqa: disable F841, report_xls namespace trick
            stock_value_start, stock_value_stop)

        c_specs = map(
            lambda x: self.render(
                x, self.col_specs_template, 'totals'), wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rt_cell_style_right)

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        self.col_specs_template.update(_p.template_changes)
        self.env = api.Environment(self.cr, self.uid, self.context)
        warehouses = self.env['stock.warehouse'].browse(data['warehouse_ids'])
        if len(warehouses) > 1:
            # create "all warehouses" overview report
            self._warehouse_report(_p, _xs, data, wb,
                                   self.env['stock.warehouse'])
        for warehouse in warehouses:
            self._warehouse_report(_p, _xs, data, wb, warehouse)


StockLevelXls(
    'report.stock.level.xls',
    'product.product',
    parser=StockLevelXlsParser)
