# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-now Noviat nv/sa (www.noviat.com).
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

import base64
import StringIO
import csv
from openerp.osv import orm, fields
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

header_fields = [
    'account', 'debit', 'credit', 'name', 'partner', 'date_maturity',
    'amount_currency', 'currency', 'tax_code', 'tax_amount',
    'analytic_account']


class aml_import(orm.TransientModel):
    _name = 'aml.import'
    _description = 'Import account move lines'
    _columns = {
        'aml_data': fields.binary('File', required=True),
        'aml_fname': fields.char('Filename', size=128, required=True),
        'csv_separator': fields.selection(
            [(',', ','), (';', ';')], 'CSV Separator', required=True),
        'decimal_separator': fields.selection(
            [('.', '.'), (',', ',')], 'Decimal Separator', required=True),
        'note': fields.text('Log'),
    }
    _defaults = {
        'aml_fname': '',
    }

    def aml_import(self, cr, uid, ids, context=None):

        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        partner_obj = self.pool.get('res.partner')
        curr_obj = self.pool.get('res.currency')
        tax_code_obj = self.pool.get('account.tax.code')
        analytic_obj = self.pool.get('account.analytic.account')
        mod_obj = self.pool.get('ir.model.data')
        dp = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')

        company_id = context['company_id']
        move_id = context['move_id']
        account_ids = account_obj.search(
            cr, uid, [('type', '!=', 'view'), ('company_id', '=', company_id)])
        accounts = account_obj.read(cr, uid, account_ids, ['code', 'name'])

        result_view = mod_obj.get_object_reference(
            cr, uid, 'account_move_import', 'aml_import_result_view')
        data = self.browse(cr, uid, ids)[0]
        aml_file = data.aml_data
        csv_separator = str(data.csv_separator)
        decimal_separator = data.decimal_separator

        err_log = ''
        header_line = False

        lines = base64.decodestring(aml_file)
        reader = csv.reader(
            StringIO.StringIO(lines), delimiter=csv_separator)
        sum_debit = sum_credit = 0.0
        amls = []

        for ln in reader:

            if not ln or ln and ln[0] and ln[0][0] in ['', '#']:
                continue

            # process header line
            if not header_line:
                if ln[0].strip().lower() not in header_fields:
                    raise orm.except_orm(
                        _('Error :'),
                        _("Error while processing the header line %s."
                          "\n\nPlease check your CSV separator as well as "
                          "the column header fields") % ln)
                else:
                    header_line = True
                    # locate first column with empty header
                    column_cnt = 0
                    account_i = debit_i = credit_i = name_i = partner_i = \
                        date_maturity_i = amount_currency_i = currency_i = \
                        tax_code_i = tax_amount_i = analytic_i = None
                    for cnt in range(len(ln)):
                        if ln[cnt] == '':
                            column_cnt = cnt
                            break
                        elif cnt == len(ln)-1:
                            column_cnt = cnt + 1
                            break
                    for i in range(column_cnt):
                        # header fields
                        header_field = ln[i].strip().lower()
                        if header_field not in header_fields:
                            err_log += '\n' + _(
                                "Invalid CSV File, Header Field '%s' "
                                "is not supported !") % ln[i]
                        # required header fields : account, debit, credit
                        elif header_field == 'account':
                            account_i = i
                        elif header_field == 'debit':
                            debit_i = i
                        elif header_field == 'credit':
                            credit_i = i
                        # optional header fields
                        elif header_field == 'name':
                            name_i = i
                        elif header_field == 'partner':
                            partner_i = i
                        elif header_field == 'date_maturity':
                            date_maturity_i = i
                        elif header_field == 'amount_currency':
                            amount_currency_i = i
                        elif header_field == 'currency':
                            currency_i = i
                        elif header_field == 'tax_code':
                            tax_code_i = i
                        elif header_field == 'tax_amount':
                            tax_amount_i = i
                        elif header_field == 'analytic_account':
                            analytic_i = i
                    for f in [(account_i, 'account'),
                              (debit_i, 'debit'), (credit_i, 'credit')]:
                        if not isinstance(f[0], int):
                            err_log += '\n' + _(
                                "Invalid CSV File, Header Field '%s' "
                                "is missing !") % f[1]

            # process data lines
            else:
                if ln and ln[0] and ln[0][0] not in ['#', '']:

                    aml_vals = {}

                    # lookup account
                    account_id = False
                    for account in accounts:
                        if ln[account_i] == account['code']:
                            account_id = account['id']
                            break
                    if not account_id:
                        err_log += '\n' + _(
                            "Error when processing line '%s', "
                            "account with code '%s' not found !"
                            ) % (ln, ln[account_i])
                    aml_vals['account_id'] = account_id

                    # debit/credit
                    try:
                        aml_vals['debit'] = round(
                            str2float(ln[debit_i], decimal_separator), dp)
                        sum_debit += aml_vals['debit']
                    except:
                        err_log += '\n' + _(
                            "Error when processing line '%s', "
                            "invalid debit value '%s' !") % (ln, ln[debit_i])
                    try:
                        aml_vals['credit'] = round(
                            str2float(ln[credit_i], decimal_separator), dp)
                        sum_credit += aml_vals['credit']
                    except:
                        err_log += '\n' + _(
                            "Error when processing line '%s', "
                            "invalid credit value '%s' !"
                            ) % (ln, ln[credit_i])

                    # name
                    aml_vals['name'] = isinstance(name_i, int) and \
                        ln[name_i] or '/'

                    # lookup partner
                    if isinstance(partner_i, int) and ln[partner_i]:
                        partner_ids = partner_obj.search(
                            cr, uid,
                            [('ref', '=', ln[partner_i]), '|',
                             ('parent_id', '=', False),
                             ('is_company', '=', True)])
                        if not partner_ids:
                            partner_ids = partner_obj.search(
                                cr, uid, [('name', '=', ln[partner_i])])
                        if not partner_ids:
                            err_log += '\n' + _(
                                "Error when processing line '%s', "
                                "partner '%s' not found !"
                                ) % (ln, ln[partner_i])
                        elif len(partner_ids) > 1:
                            err_log += '\n' + _(
                                "Error when processing line '%s', "
                                "multiple partners with reference "
                                "or name '%s' found !") % (ln, ln[partner_i])
                        else:
                            aml_vals['partner_id'] = partner_ids[0]

                    # due_date
                    if isinstance(date_maturity_i, int) and \
                            ln[date_maturity_i]:
                        aml_vals['date_maturity'] = ln[date_maturity_i]

                    amls.append((0, 0, aml_vals))

                    # amount_currency
                    if isinstance(amount_currency_i, int) and \
                            ln[amount_currency_i]:
                        aml_vals['amount_currency'] = round(
                            str2float(ln[amount_currency_i],
                                      decimal_separator),
                            dp)

                    # lookup currency
                    if isinstance(currency_i, int) and ln[currency_i]:
                        curr_ids = curr_obj.search(
                            cr, uid, [('name', '=', ln[currency_i])])
                        if not curr_ids:
                            err_log += '\n' + _(
                                "Error when processing line '%s', "
                                "currency '%s' not found !"
                                ) % (ln, ln[currency_i])
                        else:
                            aml_vals['currency_id'] = curr_ids[0]

                    # lookup tax_code
                    if isinstance(tax_code_i, int) and ln[tax_code_i]:
                        tax_code_ids = tax_code_obj.search(
                            cr, uid, [('code', '=', ln[tax_code_i])])
                        if not tax_code_ids:
                            tax_code_ids = tax_code_obj.search(
                                cr, uid, [('name', '=', ln[tax_code_i])])
                        if not tax_code_ids:
                            err_log += '\n' + _(
                                "Error when processing line '%s', "
                                "tax code '%s' not found !"
                                ) % (ln, ln[tax_code_i])
                        else:
                            aml_vals['tax_code_id'] = tax_code_ids[0]

                    # tax_amount
                    if isinstance(tax_amount_i, int) and ln[tax_amount_i]:
                        aml_vals['tax_amount'] = round(
                            str2float(ln[tax_amount_i], decimal_separator),
                            dp)

                    # lookup analytic_account
                    if isinstance(analytic_i, int) and ln[analytic_i]:
                        name_result = code_result = 0
                        # 1 = search result None
                        # 2 = search result Multiple
                        analytic_ids = analytic_obj.search(
                            cr, uid, [('name', '=', ln[analytic_i])])
                        if len(analytic_ids) == 1:
                            aml_vals['analytic_account_id'] = analytic_ids[0]
                        else:
                            name_result = not analytic_ids and 1 or 2
                            analytic_ids = analytic_obj.search(
                                cr, uid, [('code', '=', ln[analytic_i])])
                            if len(analytic_ids) == 1:
                                aml_vals['analytic_account_id'] = \
                                    analytic_ids[0]
                            else:
                                code_result = not analytic_ids and 1 or 2
                        if not aml_vals.get('analytic_account_id'):
                            if name_result == 1 and code_result == 1:
                                err_log += '\n' + _(
                                    "Error when processing line '%s', "
                                    "analytic account '%s' not found !"
                                    ) % (ln, ln[analytic_i])
                            else:
                                err_log += '\n' + _(
                                    "Error when processing line '%s', "
                                    "multiple analytic accounts found "
                                    "that match with '%s' !"
                                    ) % (ln, ln[analytic_i])

        if round(sum_debit, dp) != round(sum_credit, dp):
            err_log += '\n' + _(
                "Error in CSV file, Total Debit (%s) is "
                "different from Total Credit (%s) !"
                ) % (sum_debit, sum_credit)

        if err_log:
            self.write(cr, uid, ids[0], {'note': err_log})
            return {
                'name': _('Import File result'),
                'res_id': ids[0],
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'aml.import',
                'view_id': [result_view[1]],
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            # rewrite date to trigger store
            move_date = move_obj.read(
                cr, uid, move_id, ['date'])['date']
            move_obj.write(
                cr, uid, [move_id], {'line_id': amls, 'date': move_date})
            return {'type': 'ir.actions.act_window_close'}


def str2float(amount, decimal_separator):
    if not amount:
        return 0.0
    else:
        if decimal_separator == '.':
            return float(amount.replace(',', ''))
        else:
            return float(amount.replace('.', '').replace(',', '.'))
