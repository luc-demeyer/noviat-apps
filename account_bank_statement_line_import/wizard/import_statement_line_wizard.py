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

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import base64
import csv
from datetime import datetime
from sys import exc_info
from traceback import format_exception

from openerp import models, fields, api, _
from openerp.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class AccountBankStatementLineImport(models.TransientModel):
    _name = 'absl.import'
    _description = 'Import bank statement lines'

    absl_data = fields.Binary(string='File', required=True)
    absl_fname = fields.Char(string='Filename')
    lines = fields.Binary(
        compute='_compute_lines', string='Input Lines', required=True)
    dialect = fields.Binary(
        compute='_compute_dialect', string='Dialect', required=True)
    csv_separator = fields.Selection(
        [(',', ' . (comma)'), (';', ', (semicolon)')],
        string='CSV Separator', required=True)
    decimal_separator = fields.Selection(
        [('.', ' . (dot)'), (',', ', (comma)')],
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
    @api.depends('absl_data')
    def _compute_lines(self):
        if self.absl_data:
            self.lines = base64.decodestring(self.absl_data)

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

    @api.onchange('absl_data')
    def _onchange_absl_data(self):
        if self.lines:
            self.csv_separator = self.dialect.delimiter
            if self.csv_separator == ';':
                self.decimal_separator = ','

    @api.onchange('csv_separator')
    def _onchange_csv_separator(self):
        if self.csv_separator and self.absl_data:
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
                header = ln.lower()
        if not header:
            raise Warning(
                _("No header line found in the input file !"))
        output = input.read()
        return output, header

    def _input_fields(self):
        """
        Extend this dictionary if you want to add support for
        fields requiring pre-processing before being added to
        the statement line values dict.
        """
        res = {
            'entry date': {'method': self._handle_date},
            'date': {'method': self._handle_date, 'required': True},
            'value date': {'method': self._handle_val_date},
            'val_date': {'method': self._handle_val_date},
            'amount': {'method': self._handle_amount, 'required': True},
            'partner': {'method': self._handle_partner},
            'communication': {'method': self._handle_name},
        }
        return res

    def _get_orm_fields(self):
        absl_mod = self.env['account.bank.statement.line']
        orm_fields = absl_mod.fields_get()
        blacklist = models.MAGIC_COLUMNS + [absl_mod.CONCURRENCY_CHECK_FIELD]
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
                raise Warning(_(
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
                _logger.error(
                    _("%s, undefined field '%s' found "
                      "while importing statement lines"),
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

    def _handle_orm_char(self, field, line, statement, absl_vals,
                         orm_field=False):
        orm_field = orm_field or field
        if not absl_vals.get(orm_field):
            absl_vals[orm_field] = line[field]

    def _handle_orm_integer(self, field, line, statement, absl_vals,
                            orm_field=False):
        orm_field = orm_field or field
        if not absl_vals.get(orm_field):
            val = str2int(
                line[field], self.decimal_separator)
            if val is False:
                msg = _(
                    "Incorrect value '%s' "
                    "for field '%s' of type Integer !"
                    ) % (line[field], field)
                self._log_line_error(line, msg)
            else:
                absl_vals[orm_field] = val

    def _handle_orm_float(self, field, line, statement, absl_vals,
                          orm_field=False):
        orm_field = orm_field or field
        if not absl_vals.get(orm_field):
            absl_vals[orm_field] = str2float(
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
                absl_vals[orm_field] = val

    def _handle_orm_many2one(self, field, line, statement, absl_vals,
                             orm_field=False):
        orm_field = orm_field or field
        if not absl_vals.get(orm_field):
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
                absl_vals[orm_field] = val

    def _handle_name(self, field, line, statement, absl_vals):
        if 'name' not in absl_vals:
            absl_vals['name'] = line[field]

    def _handle_amount(self, field, line, statement, absl_vals):
        if 'amount' not in absl_vals:
            amount = str2float(line[field], self.decimal_separator)
            absl_vals['amount'] = amount

    def _handle_partner(self, field, line, statement, absl_vals):
        if not absl_vals.get('partner_id'):
            input = line[field]
            part_mod = self.env['res.partner']
            dom = ['|', ('parent_id', '=', False), ('is_company', '=', True)]
            dom_ref = dom + [('ref', '=', input)]
            partners = part_mod.search(dom_ref)
            if not partners:
                dom_name = dom + [('name', '=', input)]
                partners = part_mod.search(dom_name)
            if not partners:
                msg = _("Partner '%s' not found !") % input
                self._log_line_error(line, msg)
                return
            elif len(partners) > 1:
                msg = _("Multiple partners with Reference "
                        "or Name '%s' found !") % input
                self._log_line_error(line, msg)
                return
            else:
                partner = partners[0]
                absl_vals['partner_id'] = partner.id

    def _handle_date(self, field, line, statement, absl_vals):
        if not absl_vals.get('date'):
            dt = line[field]
            try:
                datetime.strptime(dt, '%Y-%m-%d')
                absl_vals['date'] = dt
            except:
                msg = _("Incorrect data format for field '%s' "
                        "with value '%s', "
                        " should be YYYY-MM-DD") % (field, dt)
                self._log_line_error(line, msg)

    def _handle_val_date(self, field, line, statement, absl_vals):
        if not absl_vals.get('val_date'):
            dt = line[field]
            try:
                datetime.strptime(dt, '%Y-%m-%d')
                absl_vals['val_date'] = dt
            except:
                msg = _("Incorrect data format for field '%s' "
                        "with value '%s', "
                        " should be YYYY-MM-DD") % (field, dt)
                self._log_line_error(line, msg)

    def _process_line_vals(self, line, statement, absl_vals):
        """
        Use this method if you want to check/modify the
        line input values dict before calling the statement write() method
        """
        if 'name' not in absl_vals:
            absl_vals['name'] = '/'

        all_fields = self._field_methods
        required_fields = [x for x in all_fields
                           if all_fields[x].get('required')]
        for rf in required_fields:
            if rf not in absl_vals:
                msg = _("The '%s' field is a required field "
                        "that must be correctly set.") % rf
                self._log_line_error(line, msg)

    def _process_vals(self, statement, vals):
        """
        Use this method if you want to check/modify the
        input values dict before calling the statement write() method
        """
        return vals

    @api.multi
    def absl_import(self):

        self._err_log = ''
        statement = self.env['account.bank.statement'].browse(
            self._context['active_id'])
        self._get_orm_fields()
        lines, header = self._remove_leading_lines(self.lines)
        header_fields = csv.reader(
            StringIO.StringIO(header), dialect=self.dialect).next()
        self._header_fields = self._process_header(header_fields)
        reader = csv.DictReader(
            StringIO.StringIO(lines), fieldnames=self._header_fields,
            dialect=self.dialect)

        statement_lines = []
        for line in reader:

            absl_vals = {}

            # step 1: handle codepage
            for i, hf in enumerate(self._header_fields):
                try:
                    line[hf] = line[hf].decode(self.codepage).strip()
                except:
                    tb = ''.join(format_exception(*exc_info()))
                    raise Warning(
                        _("Wrong Code Page"),
                        _("Error while processing line '%s' :\n%s")
                        % (line, tb))

            # step 2: process input fields
            for i, hf in enumerate(self._header_fields):
                if i == 0 and line[hf] and line[hf][0] == '#':
                    # lines starting with # are considered as comment lines
                    break
                if hf in self._skip_fields:
                    continue
                if line[hf] == '':
                    continue

                if self._field_methods[hf].get('orm_field'):
                    self._field_methods[hf]['method'](
                        hf, line, statement, absl_vals,
                        orm_field=self._field_methods[hf]['orm_field'])
                else:
                    self._field_methods[hf]['method'](
                        hf, line, statement, absl_vals)

            if absl_vals:
                self._process_line_vals(line, statement, absl_vals)
                statement_lines.append(absl_vals)

        vals = [(0, 0, l) for l in statement_lines]
        vals = self._process_vals(statement, vals)

        if self._err_log:
            self.note = self._err_log
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = self.env.ref(
                '%s.absl_import_view_form_result' % module)
            return {
                'name': _("Import File result"),
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'absl.import',
                'view_id': result_view.id,
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            statement.write({'line_ids': vals})
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
