# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import base64
import csv
import time
from sys import exc_info
from traceback import format_exception

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class StockLevelImport(models.TransientModel):
    _name = 'stock.level.import'
    _description = 'Stock level Import'

    stock_level_data = fields.Binary(string='File', required=True)
    stock_level_fname = fields.Char(string='Filename')
    lines = fields.Binary(
        compute='_compute_lines', string='Input Lines', required=True)
    dialect = fields.Binary(
        compute='_compute_dialect', string='Dialect', required=True)
    csv_separator = fields.Selection(
        [(',', ', (comma)'), (';', '; (semicolon)')],
        string='CSV Separator', required=True)
    decimal_separator = fields.Selection(
        [('.', '. (dot)'), (',', ', (comma)')],
        string='Decimal Separator',
        default='.', required=True)
    codepage = fields.Char(
        string='Code Page',
        default=lambda self: self._default_codepage(),
        help="Code Page of the system that has generated the csv file."
             "\nE.g. Windows-1252, utf-8")
    note = fields.Text('Log')

    @api.model
    def _default_codepage(self):
        return 'Windows-1252'

    @api.one
    @api.depends('stock_level_data')
    def _compute_lines(self):
        if self.stock_level_data:
            lines = base64.decodestring(self.stock_level_data)
            # convert windows & mac line endings to unix style
            self.lines = lines.replace('\r\n', '\n').replace('\r', '\n')

    @api.one
    @api.depends('lines', 'csv_separator')
    def _compute_dialect(self):
        if self.lines:
            try:
                self.dialect = csv.Sniffer().sniff(
                    self.lines[:128], delimiters=';,')
            except:
                # csv.Sniffer is not always reliable
                # in the detection of the delimiter
                self.dialect = csv.Sniffer().sniff(
                    '"header 1";"header 2";\r\n')
                if ',' in self.lines[128]:
                    self.dialect.delimiter = ','
                elif ';' in self.lines[128]:
                    self.dialect.delimiter = ';'
        if self.csv_separator:
            self.dialect.delimiter = str(self.csv_separator)

    @api.onchange('stock_level_data')
    def _onchange_stock_level_data(self):
        if self.lines:
            self.csv_separator = self.dialect.delimiter
            if self.csv_separator == ';':
                self.decimal_separator = ','

    @api.onchange('csv_separator')
    def _onchange_csv_separator(self):
        if self.csv_separator and self.stock_level_data:
            self.dialect.delimiter = self.csv_separator

    def _remove_leading_lines(self, lines):
        """ remove leading blank or comment lines """
        input = StringIO.StringIO(lines)
        header = False
        while not header:
            ln = input.next()
            if not ln or ln and ln[0] in [self.csv_separator, '#']:
                continue
            else:
                ln_lower = ln.lower()
                ln_set = set(ln_lower.split(self.csv_separator))
                valid = ln_set.intersection(self._input_fields())
                if not valid:
                    continue
                header = ln_lower
        if not header:
            raise UserError(
                _("No header line found in the input file !"))
        output = input.read()
        return output, header

    def _input_fields(self):
        """
        Extend this dictionary if you want to add support for
        fields requiring pre-processing before being added to
        the inventory line values dict.
        """
        res = {
            'stock location': {'method': self._handle_location},
            'location_id': {'method': self._handle_location_id,
                            'required': True},
            'product': {'method': self._handle_product},
            'product_id': {'method': self._handle_product_id,
                           'required': True},
            'product uom': {'method': self._handle_product_uom},
            'product_uom_id': {'method': self._handle_product_uom_id,
                               'required': True},
            'quantity': {'method': self._handle_quantity},
            # 'production lot': {'method': self._handle_production_lot},
        }
        return res

    def _get_orm_fields(self):
        sil_mod = self.env['stock.inventory.line']
        orm_fields = sil_mod.fields_get()
        blacklist = models.MAGIC_COLUMNS + [sil_mod.CONCURRENCY_CHECK_FIELD]
        self._orm_fields = {
            f: orm_fields[f] for f in orm_fields
            if f not in blacklist
            and not orm_fields[f].get('depends')}

    def _process_header(self, header_fields):

        self._field_methods = self._input_fields()
        self._skip_fields = []

        # header fields after blank column are considered as comments
        column_cnt = 0
        for cnt in range(len(header_fields)):
            if header_fields[cnt] == '':
                column_cnt = cnt
                break
            elif cnt == len(header_fields) - 1:
                column_cnt = cnt + 1
                break
        header_fields = header_fields[:column_cnt]

        # check for duplicate header fields
        header_fields2 = []
        for hf in header_fields:
            if hf in header_fields2:
                raise UserError(_(
                    "Duplicate header field '%s' found !"
                    "\nPlease correct the input file.")
                    % hf)
            else:
                header_fields2.append(hf)

        for i, hf in enumerate(header_fields):

            if hf in self._field_methods:
                continue

            if hf not in self._orm_fields \
                    and hf not in [self._orm_fields[f]['string'].lower()
                                   for f in self._orm_fields]:
                _logger.debug(
                    _("%s, undefined field '%s' found "
                      "while importing inventory lines"),
                    self._name, hf)
                self._skip_fields.append(hf)
                continue

            field_def = self._orm_fields.get(hf)
            if not field_def:
                for f in self._orm_fields:
                    if self._orm_fields[f]['string'].lower() == hf:
                        orm_field = f
                        field_def = self._orm_fields.get(f)
                        break
            else:
                orm_field = hf
            field_type = field_def['type']

            if field_type in ['char', 'text']:
                self._field_methods[hf] = {
                    'method': self._handle_orm_char,
                    'orm_field': orm_field,
                    }
            elif field_type == 'integer':
                self._field_methods[hf] = {
                    'method': self._handle_orm_integer,
                    'orm_field': orm_field,
                    }
            elif field_type == 'float':
                self._field_methods[hf] = {
                    'method': self._handle_orm_float,
                    'orm_field': orm_field,
                    }
            elif field_type == 'many2one':
                self._field_methods[hf] = {
                    'method': self._handle_orm_many2one,
                    'orm_field': orm_field,
                    }
            else:
                _logger.error(
                    _("%s, the import of ORM fields of type '%s' "
                      "is not supported"),
                    self._name, hf, field_type)
                self._skip_fields.append(hf)

        return header_fields

    def _log_line_error(self, line, msg):
        data = self.csv_separator.join(
            [line[hf] for hf in self._header_fields])
        self._err_log += _(
            "Error when processing line '%s'") % data + ':\n' + msg + '\n\n'

    def _handle_orm_char(self, field, line, inventory, sil_vals,
                         orm_field=False):
        orm_field = orm_field or field
        if not sil_vals.get(orm_field):
            sil_vals[orm_field] = line[field]

    def _handle_orm_integer(self, field, line, inventory, sil_vals,
                            orm_field=False):
        orm_field = orm_field or field
        if not sil_vals.get(orm_field):
            val = str2int(
                line[field], self.decimal_separator)
            if val is False:
                msg = _(
                    "Incorrect value '%s' "
                    "for field '%s' of type Integer !"
                    ) % (line[field], field)
                self._log_line_error(line, msg)
            else:
                sil_vals[orm_field] = val

    def _handle_orm_float(self, field, line, inventory, sil_vals,
                          orm_field=False):
        orm_field = orm_field or field
        if not sil_vals.get(orm_field):
            sil_vals[orm_field] = str2float(
                line[field], self.decimal_separator)

            val = str2float(
                line[field], self.decimal_separator)
            if val is False:
                msg = _(
                    "Incorrect value '%s' "
                    "for field '%s' of type Numeric !"
                    ) % (line[field], field)
                self._log_line_error(line, msg)
            else:
                sil_vals[orm_field] = val

    def _handle_orm_many2one(self, field, line, inventory, sil_vals,
                             orm_field=False):
        orm_field = orm_field or field
        if not sil_vals.get(orm_field):
            val = str2int(
                line[field], self.decimal_separator)
            if val is False:
                msg = _(
                    "Incorrect value '%s' "
                    "for field '%s' of type Many2One !"
                    "\nYou should specify the database key "
                    "or contact your IT department "
                    "to add support for this field."
                    ) % (line[field], field)
                self._log_line_error(line, msg)
            else:
                sil_vals[orm_field] = val

    def _handle_location_id(self, field, line, inventory, sil_vals):
        sil_vals['location_id'] = line[field]

    def _handle_location(self, field, line, inventory, sil_vals):
        if not sil_vals.get('location_id'):
            loc_mod = self.env['stock.location']
            input = line[field]
            domain = [('usage', '=', 'internal'),
                      ('company_id', '=', inventory.company_id.id),
                      ('complete_name', '=', input)]
            locations = loc_mod.search(domain)
            if len(locations) == 1:
                sil_vals['location_id'] = locations.id
            elif len(locations) > 1:
                msg = _("Multiple locations found "
                        "that match with '%s' !") % input
                self._log_line_error(line, msg)
            elif not locations:
                msg = _("Invalid location '%s' !") % input
                self._log_line_error(line, msg)

    def _handle_product_id(self, field, line, inventory, sil_vals):
        sil_vals['product_id'] = line[field]

    def _handle_product(self, field, line, inventory, sil_vals):
        if not sil_vals.get('product_id'):
            input = line[field]
            prod_mod = self.env['product.product']
            products = prod_mod.search([
                ('default_code', '=', input)])
            if not products:
                products = prod_mod.search(
                    [('name', '=', input)])
            if not products:
                msg = _("Product '%s' not found !") % input
                self._log_line_error(line, msg)
                return
            elif len(products) > 1:
                msg = _("Multiple products with Internal Reference "
                        "or Name '%s' found !") % input
                self._log_line_error(line, msg)
                return
            else:
                product = products[0]
                sil_vals['product_id'] = product.id

    def _handle_product_uom_id(self, field, line, inventory, sil_vals):
        sil_vals['product_uom_id'] = line[field]

    def _handle_product_uom(self, field, line, inventory, sil_vals):
        if not sil_vals.get('product_uom_id'):
            name = line[field]
            uom = self.env['product.uom'].search([
                ('name', '=ilike', name)])
            if uom:
                sil_vals['product_uom_id'] = uom[0].id
            else:
                msg = _("Unit of Measure with name '%s' not found !") % name
                self._log_line_error(line, msg)

    def _handle_quantity(self, field, line, inventory, sil_vals):
        if not sil_vals.get('product_qty'):
            qty = line[field]
            sil_vals['product_qty'] = str2float(qty, self.decimal_separator) \
                or 0.0

    def _process_line_vals(self, line, inventory, sil_vals):
        """
        Use this method if you want to check/modify the
        line input values dict before calling the inventory write() method
        """
        all_fields = self._field_methods
        required_fields = [x for x in all_fields
                           if all_fields[x].get('required')]
        for rf in required_fields:
            if rf not in sil_vals:
                msg = _("The '%s' field is a required field "
                        "that must be correctly set.") % rf
                self._log_line_error(line, msg)

    def _process_vals(self, inventory, vals):
        """
        Use this method if you want to check/modify the
        input values dict before calling the inventory write() method
        """
        return vals

    @api.multi
    def stock_level_import(self):

        time_start = time.time()
        self._err_log = ''
        inventory = self.env['stock.inventory'].browse(
            self._context['active_id'])
        self._get_orm_fields()
        lines, header = self._remove_leading_lines(self.lines)
        header_fields = csv.reader(
            StringIO.StringIO(header), dialect=self.dialect).next()
        self._header_fields = self._process_header(header_fields)
        reader = csv.DictReader(
            StringIO.StringIO(lines), fieldnames=self._header_fields,
            dialect=self.dialect)

        lines = []
        for line in reader:

            sil_vals = {}

            # step 1: handle codepage
            for i, hf in enumerate(self._header_fields):
                try:
                    line[hf] = line[hf].decode(self.codepage).strip()
                except:
                    tb = ''.join(format_exception(*exc_info()))
                    raise UserError(
                        _("Wrong Code Page"),
                        _("Error while processing line '%s' :\n%s")
                        % (line, tb))

            # step 2: process input fields
            header_reversed = reversed(self._header_fields)
            # we process the header in reversed order for performance reasons.
            # By doing so, the *_id fields generated by the
            # stock_level_export_xls module are processed first,
            # thereby removing the need for database lookups.
            for i, hf in enumerate(header_reversed):
                if i == 0 and line[hf] and line[hf][0] == '#':
                    # lines starting with # are considered as comment lines
                    break
                if hf in self._skip_fields:
                    continue
                if line[hf] == '':
                    continue

                if self._field_methods[hf].get('orm_field'):
                    self._field_methods[hf]['method'](
                        hf, line, inventory, sil_vals,
                        orm_field=self._field_methods[hf]['orm_field'])
                else:
                    self._field_methods[hf]['method'](
                        hf, line, inventory, sil_vals)

            if sil_vals:
                self._process_line_vals(line, inventory, sil_vals)
                lines.append(sil_vals)

        vals = [(0, 0, l) for l in lines]
        vals = self._process_vals(inventory, vals)

        if self._err_log:
            self.note = self._err_log
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = self.env.ref(
                '%s.stock_level_import_view_form_result' % module)
            return {
                'name': _("Import File result"),
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.level.import',
                'view_id': result_view.id,
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            ctx = dict(self._context, novalidate=True)
            inventory.with_context(ctx).write({
                'line_ids': vals,
                'state': 'confirm',
                'date': fields.Datetime.now(),
                })
            import_time = time.time() - time_start
            _logger.warn(
                'stock.inventory %s import time = %.3f seconds',
                inventory.name, import_time)
            return {'type': 'ir.actions.act_window_close'}


def str2float(amount, decimal_separator):
    if not amount:
        return 0.0
    try:
        if decimal_separator == '.':
            return float(amount.replace(',', ''))
        else:
            return float(amount.replace('.', '').replace(',', '.'))
    except:
        return False


def str2int(amount, decimal_separator):
    if not amount:
        return 0
    try:
        if decimal_separator == '.':
            return int(amount.replace(',', ''))
        else:
            return int(amount.replace('.', '').replace(',', '.'))
    except:
        return False
