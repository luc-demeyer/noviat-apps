# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
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

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

import logging
_logger = logging.getLogger(__name__)


class InvoiceLineImport(models.TransientModel):
    _name = 'ail.import'
    _description = 'Import invoice lines'

    ail_data = fields.Binary(string='File', required=True)
    ail_fname = fields.Char(string='Filename')
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
    @api.depends('ail_data')
    def _compute_lines(self):
        if self.ail_data:
            lines = base64.decodestring(self.ail_data)
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

    @api.onchange('ail_data')
    def _onchange_ail_data(self):
        if self.lines:
            self.csv_separator = self.dialect.delimiter
            if self.csv_separator == ';':
                self.decimal_separator = ','

    @api.onchange('csv_separator')
    def _onchange_csv_separator(self):
        if self.csv_separator and self.ail_data:
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
            raise UserError(
                _("No header line found in the input file !"))
        output = input.read()
        return output, header

    def _input_fields(self):
        """
        Extend this dictionary if you want to add support for
        fields requiring pre-processing before being added to
        the invoice line values dict.
        """
        res = {
            'description': {'method': self._handle_description},
            'product': {'method': self._handle_product},
            'unit of measure': {'method': self._handle_uos},
            'account': {'method': self._handle_account},
            'quantity': {'method': self._handle_quantity},
            'unit price': {'method': self._handle_unit_price},
            'taxes': {'method': self._handle_taxes},
            'analytic account': {'method': self._handle_analytic_account},
        }
        return res

    def _get_orm_fields(self):
        ail_mod = self.env['account.invoice.line']
        orm_fields = ail_mod.fields_get()
        blacklist = models.MAGIC_COLUMNS + [ail_mod.CONCURRENCY_CHECK_FIELD]
        self._orm_fields = {
            f: orm_fields[f] for f in orm_fields
            if f not in blacklist and not orm_fields[f].get('depends')}

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

            if hf in self._field_methods \
                    and self._field_methods[hf].get('method'):
                continue

            if hf not in self._orm_fields \
                    and hf not in [self._orm_fields[f]['string'].lower()
                                   for f in self._orm_fields]:
                _logger.error(
                    _("%s, undefined field '%s' found "
                      "while importing invoice lines"),
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

            try:
                ft = field_type == 'text' and 'char' or field_type
                self._field_methods[hf] = {
                    'method': getattr(self, '_handle_orm_%s' % ft),
                    'orm_field': orm_field,
                    }
            except AttributeError:
                _logger.error(
                    _("%s, field '%s', "
                      "the import of ORM fields of type '%s' "
                      "is not supported"),
                    self._name, hf, field_type)
                self._skip_fields.append(hf)

        return header_fields

    def _log_line_error(self, line, msg):
        data = self.csv_separator.join(
            [line[hf] for hf in self._header_fields])
        self._err_log += _(
            "Error when processing line '%s'") % data + ':\n' + msg + '\n\n'

    def _handle_orm_char(self, field, line, invoice, ail_vals,
                         orm_field=False):
        orm_field = orm_field or field
        if not ail_vals.get(orm_field):
            ail_vals[orm_field] = line[field]

    def _handle_orm_integer(self, field, line, move, ail_vals,
                            orm_field=False):
        orm_field = orm_field or field
        if not ail_vals.get(orm_field):
            val = str2int(
                line[field], self.decimal_separator)
            if val is False:
                msg = _(
                    "Incorrect value '%s' "
                    "for field '%s' of type Integer !"
                    ) % (line[field], field)
                self._log_line_error(line, msg)
            else:
                ail_vals[orm_field] = val

    def _handle_orm_float(self, field, line, move, ail_vals,
                          orm_field=False):
        orm_field = orm_field or field
        if not ail_vals.get(orm_field):
            ail_vals[orm_field] = str2float(
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
                ail_vals[orm_field] = val

    def _handle_orm_boolean(self, field, line, move, ail_vals,
                            orm_field=False):
        orm_field = orm_field or field
        if not ail_vals.get(orm_field):
            val = line[field].capitalize()
            if val in ['', '0', 'False']:
                val = False
            elif val in ['1', 'True']:
                val = True
            if isinstance(val, basestring):
                msg = _(
                    "Incorrect value '%s' "
                    "for field '%s' of type Boolean !"
                    ) % (line[field], field)
                self._log_line_error(line, msg)
            else:
                ail_vals[orm_field] = val

    def _handle_orm_many2one(self, field, line, move, ail_vals,
                             orm_field=False):
        orm_field = orm_field or field
        if not ail_vals.get(orm_field):
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
                ail_vals[orm_field] = val

    def _handle_description(self, field, line, invoice, ail_vals):
        if not ail_vals.get('name'):
            ail_vals['name'] = line['description'] or '/'

    def _handle_quantity(self, field, line, invoice, ail_vals):
        if not ail_vals.get('quantity'):
            qty = line[field]
            ail_vals['quantity'] = str2float(qty, self.decimal_separator) or 1

    def _handle_unit_price(self, field, line, invoice, ail_vals):
        if not ail_vals.get('price_unit'):
            price_unit = line[field]
            ail_vals['price_unit'] = str2float(
                price_unit, self.decimal_separator)

    def _handle_product(self, field, line, invoice, ail_vals):
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
            ail_vals['product_id'] = product.id

        # convert input fields before calling product_id_change
        # to prevent overwrite of input data
        if line.get('quantity') and 'quantity' not in ail_vals:
            self._field_methods['quantity']['method'](
                'quantity', line, invoice, ail_vals)
        qty = ail_vals.get('quantity') or 1

        if line.get('unit of measure') and 'uos_id' not in ail_vals:
            self._field_methods['unit of measure']['method'](
                'unit of measure', line, invoice, ail_vals)
        elif line.get('uos_id') and 'uos_id' not in ail_vals:
            self._field_methods['uos_id']['method'](
                'uos_id', line, invoice, ail_vals)
        uom_id = ail_vals.get('uos_id')

        if line.get('description') and 'name' not in ail_vals:
            self._field_methods['description']['method'](
                'description', line, invoice, ail_vals)
        name = ail_vals.get('name') or ''

        if line.get('unit price') and 'price_unit' not in ail_vals:
            self._field_methods['unit price']['method'](
                'unit price', line, invoice, ail_vals)
        elif line.get('price_unit') and 'price_unit' not in ail_vals:
            self._field_methods['price_unit']['method'](
                'price_unit', line, invoice, ail_vals)
        price_unit = ail_vals.get('price_unit') or 0.0

        if line.get('taxes') and 'invoice_line_tax_id' not in ail_vals:
            self._field_methods['taxes']['method'](
                'taxes', line, invoice, ail_vals)

        if line.get('analytic account') \
                and 'account_analytic_id' not in ail_vals:
            self._field_methods['analytic account']['method'](
                'analytic account', line, invoice, ail_vals)

        res = self.env['account.invoice.line'].product_id_change(
            product.id, uom_id, qty=qty, name=name,
            type=invoice.type, partner_id=invoice.partner_id.id,
            fposition_id=invoice.fiscal_position.id, price_unit=price_unit,
            currency_id=invoice.currency_id.id,
            company_id=invoice.company_id.id)

        for val in res['value']:
            # do not replace fields which have been set already
            if val not in ail_vals:
                if val == 'invoice_line_tax_id':
                    ail_vals[val] = [(6, 0, res['value'][val])]
                else:
                    ail_vals[val] = res['value'][val]

    def _handle_uos(self, field, line, invoice, ail_vals):
        if not ail_vals.get('uos_id'):
            name = line[field]
            uos = self.env['product.uom'].search([
                ('name', '=ilike', name)])
            if uos:
                ail_vals['uos_id'] = uos[0].id
            else:
                msg = _("Unit of Measure with name '%s' not found !") % name
                self._log_line_error(line, msg)

    def _handle_account(self, field, line, invoice, ail_vals):
        if not ail_vals.get('account_id'):
            code = line[field]
            if code in self._accounts_dict:
                ail_vals['account_id'] = self._accounts_dict[code]
            else:
                msg = _("Account with code '%s' not found !") % code
                self._log_line_error(line, msg)

    def _handle_taxes(self, field, line, invoice, ail_vals):
        if not ail_vals.get('invoice_line_tax_id'):
            input = line[field].split(',')
            tax_ids = []
            for t in input:
                tax_in = t.strip()
                tax = self.env['account.tax'].search([
                    ('description', '=', tax_in)])
                if not tax:
                    tax = self.env['account.tax'].search([
                        ('name', '=ilike', tax_in)])
                if tax:
                    tax_ids.append(tax[0].id)
                else:
                    msg = _("Tax with Code or Name '%s' not found !") % t
                    self._log_line_error(line, msg)
            if tax_ids:
                ail_vals['invoice_line_tax_id'] = [(6, 0, tax_ids)]

    def _handle_analytic_account(self, field, line, invoice, ail_vals):
        if not ail_vals.get('account_analytic_id'):
            ana_mod = self.env['account.analytic.account']
            input = line[field]
            domain = [('type', '!=', 'view'),
                      ('company_id', '=', invoice.company_id.id),
                      ('state', 'not in', ['close', 'cancelled'])]
            analytic_accounts = ana_mod.search(
                domain + [('code', '=', input)])
            if len(analytic_accounts) == 1:
                ail_vals['account_analytic_id'] = analytic_accounts.id
            else:
                analytic_accounts = ana_mod.search(
                    domain + [('name', '=', input)])
                if len(analytic_accounts) == 1:
                    ail_vals['account_analytic_id'] = analytic_accounts.id
            if not analytic_accounts:
                msg = _("Invalid Analytic Account '%s' !") % input
                self._log_line_error(line, msg)
            elif len(analytic_accounts) > 1:
                msg = _("Multiple Analytic Accounts found "
                        "that match with '%s' !") % input
                self._log_line_error(line, msg)

    def _process_line_vals(self, line, invoice, ail_vals):
        if 'name' not in ail_vals:
            ail_vals['name'] = '/'
        if 'account_id' not in ail_vals:
            msg = _("The Account field has not been defined.")
            self._log_line_error(line, msg)

    def _process_vals(self, invoice, vals):
        """
        Use this method if you want to check/modify the
        input values before calling the invoice write() method
        """
        return vals

    @api.multi
    def ail_import(self):

        time_start = time.time()
        self._err_log = ''
        invoice = self.env['account.invoice'].browse(
            self._context['active_id'])
        accounts = self.env['account.account'].search([
            ('type', 'not in', ['view', 'consolidation', 'closed']),
            ('company_id', '=', invoice.company_id.id)
            ])
        self._accounts_dict = {a.code: a.id for a in accounts}
        self._get_orm_fields()
        lines, header = self._remove_leading_lines(self.lines)
        header_fields = csv.reader(
            StringIO.StringIO(header), dialect=self.dialect).next()
        self._header_fields = self._process_header(header_fields)
        reader = csv.DictReader(
            StringIO.StringIO(lines), fieldnames=self._header_fields,
            dialect=self.dialect)

        inv_lines = []
        for line in reader:

            ail_vals = {}

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
                        hf, line, invoice, ail_vals,
                        orm_field=self._field_methods[hf]['orm_field'])
                else:
                    self._field_methods[hf]['method'](
                        hf, line, invoice, ail_vals)

            if ail_vals:
                self._process_line_vals(line, invoice, ail_vals)
                inv_lines.append(ail_vals)

        vals = [(0, 0, l) for l in inv_lines]
        vals = self._process_vals(invoice, vals)

        if self._err_log:
            self.note = self._err_log
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = self.env.ref(
                '%s.ail_import_view_form_result' % module)
            return {
                'name': _("Import File result"),
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'ail.import',
                'view_id': result_view.id,
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            invoice.write({'invoice_line': vals})
            import_time = time.time() - time_start
            _logger.warn(
                'account.invoice (id: %s) import time = %.3f seconds',
                invoice.id, import_time)
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
