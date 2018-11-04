# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# TO REMOVE after merge of https://github.com/OCA/reporting-engine/pull/251
from types import CodeType
from datetime import datetime

import logging

from odoo import fields, _
from odoo.tools.translate import translate
from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
    import AbstractReportXlsx
from odoo.exceptions import UserError
from odoo.report import report_sxw

_logger = logging.getLogger(__name__)

# TODO: add po-files for excel cell strings
IR_TRANSLATION_NAME = 'stock.level.xls'


class StockLevelXls(AbstractReportXlsx):

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _define_formats(self, wb):
        super(StockLevelXls, self)._define_formats(wb)
        # TODO: create PR on report_xlsx_helper to add
        # tcell grey formats
        border_grey = '#D3D3D3'
        border = {'border': True, 'border_color': border_grey}
        bg_grey = '#D3D3D3'
        num_format = '#,##0.00'
        tcell_grey = dict(border, bg_color=bg_grey)
        self.format_tcell_grey_left = wb.add_format(tcell_grey)
        self.format_tcell_grey_center = wb.add_format(
            dict(tcell_grey, align='center'))
        self.format_tcell_grey_right = wb.add_format(
            dict(tcell_grey, align='right'))
        self.format_tcell_grey_amount_left = wb.add_format(
            dict(tcell_grey, num_format=num_format, align='left'))
        self.format_tcell_grey_amount_center = wb.add_format(
            dict(tcell_grey, num_format=num_format, align='center'))
        self.format_tcell_grey_amount_right = wb.add_format(
            dict(tcell_grey, num_format=num_format, align='right'))

    def _get_ws_params(self, wb, data, wiz):
        stock_level_date = wiz.import_compatible \
            and False or wiz.stock_level_date
        warehouses = self.env['stock.warehouse'].browse(
            self.env.context['warehouse_ids'])
        data.update({
            'stock_level_date': stock_level_date,
            'warehouses': warehouses,
        })
        ws_params = []
        if len(warehouses) > 1:
            # create "all warehouses" overview report
            ws_params.append(self._get_warehouse_ws_params(
                wb, data, wiz, self.env['stock.warehouse']))
        for warehouse in warehouses:
            params = self._get_warehouse_ws_params(wb, data, wiz, warehouse)
            if params:
                ws_params.append(params)
        return ws_params

    def _get_warehouse_ws_params(self, wb, data, wiz, warehouse):
        report_lines = self._get_stock_data(data, wiz, warehouse)
        if warehouse:
            sheet_name = warehouse.name
            report_name = self._("Warehouse") + ' ' + sheet_name + ' - '
            if not report_lines and len(data['warehouses']) > 1:
                return
        else:
            sheet_name = self._("All Warehouses")
            report_name = sheet_name + ' - '
        date_dt = fields.Datetime.from_string(
            data['stock_level_date'] or fields.Datetime.now())
        date_tz = fields.Datetime.context_timestamp(self.env.user, date_dt)
        report_name += self._("Stock Levels at {}").format(
            fields.Datetime.to_string(date_tz))

        wl = self.env['product.product']._stock_level_export_xls_fields()
        if wiz.import_compatible:
            for x in ['location', 'location_id',
                      'product_id', 'product_uom_id']:
                if x not in wl:
                    wl.append(x)
            all_locations = self.env['stock.location'].search(
                [('id', 'child_of', [wiz.location_id.id])])
            if all_locations != wiz.location_id:
                report_lines = self._report_lines_per_location(
                    report_lines, all_locations, wiz)

        if not wiz.add_cost:
            if 'cost_at_date' in wl:
                wl.remove('cost_at_date')
            if 'qty_x_cost' in wl:
                wl.remove('qty_x_cost')

        return {
            'ws_name': sheet_name,
            'generate_ws_method': '_warehouse_report',
            'title': report_name,
            'wanted_list': wl,
            'col_specs': self._get_template(),
            'warehouse': warehouse,
            'report_lines': report_lines,
        }

    def _xls_export_domain(self, wiz):
        ctx = self.env.context
        if wiz.product_type:
            domain = [('type', '=', wiz.product_type)]
        else:
            domain = [('type', 'in', ['product', 'consu'])]
        domain += [
            '|', ('company_id', '=', wiz.company_id.id),
            ('company_id', '=', False)]
        if wiz.categ_id:
            domain.append(('categ_id', 'child_of', wiz.categ_id.id))
        if wiz.product_id:
            domain.append(('id', '=', wiz.product_id.id))
        if wiz.product_select == 'select':
            if ctx.get('active_model') == 'product.product':
                domain.append(('id', 'in', ctx.get('active_ids')))
            elif ctx.get('active_model') == 'product.template':
                domain.append(
                    ('product_tmpl_id', 'in', ctx.get('active_ids')))
        return domain

    def _get_stock_data_context(self, data, wiz, warehouse):
        ctx = self.env.context.copy()
        ctx['force_company'] = wiz.company_id.id
        if warehouse:
            ctx['warehouse'] = warehouse.id
        ctx['to_date'] = data['stock_level_date'] or fields.Datetime.now()
        ctx['active_test'] = False
        if wiz.lot_id:
            ctx.update({'lot_id': wiz.lot_id.id})
        if wiz.owner_id:
            ctx.update({'owner_id': wiz.owner_id.id})
        if wiz.package_id:
            ctx.update({'package_id': wiz.owner_id.id})
        if wiz.add_cost:
            ctx.update({'add_cost_at_date': True})
        if wiz.location_id:
            ctx.update({'location': wiz.location_id.id})
        return ctx

    def _get_stock_data(self, data, wiz, warehouse):
        ctx = self._get_stock_data_context(data, wiz, warehouse)
        product_domain = self._xls_export_domain(wiz)
        products = self.env['product.product'].with_context(ctx).search(
            product_domain)
        product_lines = [
            {'product': product, 'location': wiz.location_id}
            for product in products]
        cost_qty = products._compute_cost_and_qty_available_at_date()
        report_lines = []
        for line in product_lines:
            product = line['product']
            qty = cost_qty[product.id]['qty_available']
            if not qty and not wiz.import_compatible:
                # Drop empty lines unless the output is intended for
                # import with new inventory values.
                continue
            line['qty_available_at_date'] = qty
            line['cost_at_date'] = cost_qty[product.id].get('cost')
            report_lines.append(line)
        return report_lines

    def _report_lines_per_location(self, lines_in, all_locations, wiz):
        """
        Query on quants to split out the lines per location.
        This is a refinement of the first query which sums up
        child location quantities into the parent location.
        This approach is as a consequence not optimal from a performance
        standpoint but acceptable since it's only called for
        inventory update purposes ('import_compatible' flag set)
        and hence never company wide (parent location is a required field
        for inventory update export).
        Combining this query into the first query would make this first query
        more complex and as a consequence slower and harder to maintain.
        """
        if all_locations == wiz.location_id:
            return lines_in
        lines_out = []
        dom = [('company_id', '=', wiz.company_id.id)]
        if wiz.lot_id:
            dom.append(('prod_lot_id', '=', wiz.lot_id.id))
        if wiz.owner_id:
            dom.append(('owner_id', '=', wiz.owner_id.id))
        if wiz.package_id:
            dom.append(('package_id', '=', wiz.package_id.id))
        for line_in in lines_in:
            pdom = dom + [('product_id', '=', line_in['product'].id)]
            for location in all_locations:
                ldom = pdom + [('location_id', '=', location.id)]
                qty = self.env['stock.quant'].read_group(
                    ldom, ['qty', 'product_id'], ['product_id'])
                if qty:
                    qty = qty[0]['qty']
                    line_out = dict(
                        line_in, qty_available_at_date=qty, location=location)
                    lines_out.append(line_out)
        return lines_out

    def _get_template(self):

        template = {
            'location': {
                'header': {
                    'type': 'string',
                    'value': self._('Stock Location'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render(
                        "line['location'] and line['location'].complete_name "
                        "or ''"
                    ),
                },
                'width': 42,
            },
            'ref': {
                'header': {
                    'type': 'string',
                    'value': self._('Product Reference'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render(
                        "line['product'].default_code or ''"),
                },
                'width': 42,
            },
            'name': {
                'header': {
                    'type': 'string',
                    'value': self._('Product Name'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render("line['product'].name"),
                },
                'width': 42,
            },
            'category': {
                'header': {
                    'type': 'string',
                    'value': self._('Product Category'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render("line['product'].categ_id.name"),
                },
                'width': 42,
            },
            'uom': {
                'header': {
                    'type': 'string',
                    'value': self._('Product UOM'),
                },
                'lines': {
                    'type': 'string',
                    'value': self._render("line['product'].uom_id.name"),
                },
                'width': 18,
            },
            'quantity': {
                'header': {
                    'type': 'string',
                    'value': self._('Quantity'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'number',
                    'value': self._render("line['qty_available_at_date']"),
                    'format': self._render("format_tcell_amount_right"),
                },
                'width': 18,
            },
            'cost_at_date': {
                'header': {
                    'type': 'string',
                    'value': self._('Cost'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'number',
                    'value': self._render("line['cost_at_date']"),
                    'format': self._render("format_tcell_amount_right"),
                },
                'width': 18,
            },
            'qty_x_cost': {
                'header': {
                    'type': 'string',
                    'value': self._('Qty x Cost'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'formula',
                    'value': self._render("stock_value_formula"),
                    'format': self._render("format_tcell_amount_right"),
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("total_value_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'location_id': {
                'header': {
                    'type': 'string',
                    'value': 'location_id',
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'number',
                    'value': self._render("line['location'].id"),
                    'format': self._render("format_tcell_right"),
                },
                'width': 13,
            },
            'product_id': {
                'header': {
                    'type': 'string',
                    'value': 'product_id',
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'number',
                    'value': self._render("line['product'].id"),
                    'format': self._render("format_tcell_right"),
                },
                'width': 13,
            },
            'product_uom_id': {
                'header': {
                    'type': 'string',
                    'value': 'uom_id',
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'number',
                    'value': self._render("line['product'].uom_id.id"),
                    'format': self._render("format_tcell_right"),
                },
                'width': 13,
            },
            'active': {
                'header': {
                    'type': 'string',
                    'value': self._('Active'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'type': 'string',
                    'value': self._render(
                        "line['product'].active and 'Y' or 'N'"),
                    'format': self._render("format_tcell_center"),
                },
                'width': 8,
            },
        }
        template.update(
            self.env['product.product']._stock_level_export_xls_template())
        return template

    def _warehouse_report(self, workbook, ws, ws_params, data, wiz):

        ws.set_landscape()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        report_lines = ws_params['report_lines']
        wanted_list = ws_params['wanted_list']

        cost_pos = 'cost_at_date' in wanted_list \
            and wanted_list.index('cost_at_date')
        quantity_pos = 'quantity' in wanted_list \
            and wanted_list.index('quantity')
        stock_value_pos = 'qty_x_cost' in wanted_list \
            and wanted_list.index('qty_x_cost')
        if not (cost_pos and quantity_pos) and 'qty_x_cost' in wanted_list:
            raise UserError(
                _("Customization Error !"),
                _("The 'Qty x Cost' field is a calculated XLS field "
                  "requiring the presence of "
                  "the 'Quantity' and 'Cost' fields!"))

        self._set_column_width(ws, ws_params)
        row_pos = 0

        # Title
        row_pos = self._write_ws_title(ws, row_pos, ws_params)

        # Filters
        filter = False
        if wiz.location_id:
            filter = True
            filter_text = (
                self._("Location") + ': ' + wiz.location_id.display_name)
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if wiz.owner_id:
            filter = True
            filter_text = (
                self._("Owner") + ': ' + wiz.owner_id.name)
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if wiz.categ_id:
            filter = True
            filter_text = (
                self._("Product Category") + ': ' + wiz.categ_id.name)
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if wiz.product_id:
            filter = True
            filter_text = (
                self._("Product") + ': ' + wiz.product_id.display_name)
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if wiz.lot_id:
            filter = True
            filter_text = (
                self._("Lot") + ': ' + wiz.lot_id.name)
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if wiz.package_id:
            filter = True
            filter_text = (
                self._("Package") + ': ' + wiz.package_id.name)
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if wiz.product_type != 'product':
            filter = True
            if wiz.product_type == 'consu':
                filter_text = (
                    self._("Product Type") + ': ' + self._('Consumable'))
            else:
                filter_text = (
                    self._("Product Types") + ': '
                    + self._('Consumables and Stockables'))
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if wiz.product_select == 'select':
            filter = True
            filter_text = (
                 self._("Products") + ': ' + self._("Selected Products"))
            ws.write_string(
                row_pos, 0, filter_text, self.format_left_bold)
            row_pos += 1
        if filter:
            row_pos += 1

        if not report_lines:
            no_entries = self._(
                "No product records with stock found for your selection.")
            row_pos = ws.write_string(
                row_pos, 0, no_entries, self.format_left_bold)
            return

        # Column headers
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)
        ws.freeze_panes(row_pos, 0)

        # Report lines
        for line in report_lines:
            cost_cell = self._rowcol_to_cell(row_pos, cost_pos)
            quantity_cell = self._rowcol_to_cell(row_pos, quantity_pos)
            stock_value_formula = cost_cell + '*' + quantity_cell
            if line['product'].active:
                default_format = self.format_tcell_left
                format_tcell_center = self.format_tcell_center
                format_tcell_right = self.format_tcell_right
                format_tcell_amount_right = self.format_tcell_amount_right
            else:
                default_format = self.format_tcell_grey_left
                format_tcell_center = self.format_tcell_grey_center
                format_tcell_right = self.format_tcell_grey_right
                format_tcell_amount_right = self.format_tcell_grey_amount_right
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={
                    'line': line,
                    'stock_value_formula': stock_value_formula,
                    'format_tcell_center': format_tcell_center,
                    'format_tcell_right': format_tcell_right,
                    'format_tcell_amount_right': format_tcell_amount_right,
                },
                default_format=default_format)

        # Totals
        line_cnt = len(report_lines)
        stock_value_start = self._rowcol_to_cell(
            row_pos - line_cnt, stock_value_pos)
        stock_value_stop = self._rowcol_to_cell(row_pos - 1, stock_value_pos)
        total_value_formula = 'SUM({}:{})'.format(
            stock_value_start, stock_value_stop)

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'total_value_formula': total_value_formula,
            },
            default_format=self.format_theader_yellow_left)

    #TOREMOVE after merge of https://github.com/OCA/reporting-engine/pull/251
    def _write_line(self, ws, row_pos, ws_params, col_specs_section=None,
                    render_space=None, default_format=None):
        """
        Write a line with all columns included in the 'wanted_list'.
        Use the entry defined by the col_specs_section.
        An empty cell will be written if no col_specs_section entry
        for a column.
        """
        col_specs = ws_params.get('col_specs')
        wl = ws_params.get('wanted_list') or []
        pos = 0
        for col in wl:
            if col not in col_specs:
                raise UserError(_(
                    "Programming Error:\n\n"
                    "The '%s' column is not defined the worksheet "
                    "column specifications.") % col)
            colspan = col_specs[col].get('colspan') or 1
            cell_spec = col_specs[col].get(col_specs_section) or {}
            if not cell_spec:
                cell_value = None
                cell_type = 'blank'
                cell_format = default_format
            else:
                cell_value = cell_spec.get('value')
                if isinstance(cell_value, CodeType):
                    cell_value = self._eval(cell_value, render_space)
                cell_type = cell_spec.get('type')
                cell_format = cell_spec.get('format') or default_format
                if not cell_type:
                    # test bool first since isinstance(val, int) returns
                    # True when type(val) is bool
                    if isinstance(cell_value, bool):
                        cell_type = 'boolean'
                    elif isinstance(cell_value, basestring):
                        cell_type = 'string'
                    elif isinstance(cell_value, (int, long, float)):
                        cell_type = 'number'
                    elif isinstance(cell_value, datetime):
                        cell_type = 'datetime'
                    else:
                        if not cell_value:
                            cell_type = 'blank'
                        else:
                            msg = _(
                                "%s, _write_line : programming error "
                                "detected while processing "
                                "col_specs_section %s, column %s"
                            ) % (__name__, col_specs_section, col)
                            if cell_value:
                                msg += _(", cellvalue %s")
                            raise UserError(msg)
            colspan = cell_spec.get('colspan') or colspan
            args_pos = [row_pos, pos]
            args_data = [cell_value]
            if cell_format:
                if isinstance(cell_format, CodeType):
                    cell_format = self._eval(cell_format, render_space)
                args_data.append(cell_format)
            if colspan > 1:
                args_pos += [row_pos, pos + colspan - 1]
                args = args_pos + args_data
                ws.merge_range(*args)
            else:
                ws_method = getattr(ws, 'write_%s' % cell_type)
                args = args_pos + args_data
                ws_method(*args)
            pos += colspan

        return row_pos + 1


StockLevelXls(
    'report.stock.level.xls',
    'wiz.export.stock.level',
    parser=report_sxw.rml_parse)
