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

from datetime import datetime
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import orm
from openerp.addons.account.report.account_financial_report import report_account_common
import logging
_logger = logging.getLogger(__name__)


class accounting_report(orm.TransientModel):
    _inherit = 'accounting.report'

    def _build_contexts(self, cr, uid, ids, data, context=None):
        result = super(accounting_report, self)._build_contexts(cr, uid, ids, data, context=context)
        account_report_id = self.read(cr, uid, ids, ['account_report_id'], context=context)[0]['account_report_id'][0]
        mod_obj = self.pool.get('ir.model.data')
        module = 'l10n_be_coa_multilang'
        xml_ids = ['account_financial_report_BE_2_FULL', 'account_financial_report_BE_3_FULL']
        be_legal_report_ids = []
        for xml_id in xml_ids:
            be_legal_report_ids.append(mod_obj.get_object_reference(cr, uid, module, xml_id)[1])
        if account_report_id in be_legal_report_ids:
            result.update({'get_children_by_sequence': True})
        return result


class report_financial_parser(report_account_common):

    def set_context(self, objects, data, ids, report_type=None):
        report_date = datetime_field.context_timestamp(self.cr, self.uid,
            datetime.now(), self.context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.localcontext.update({
            'report_date': report_date,
        })
        super(report_financial_parser, self).set_context(objects, data, ids, report_type)

    def get_lines(self, data):
        """
        Method copied from account module in order to add code to vals.
        TO DO : Pull Request
        """
        lines = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        ids2 = self.pool.get('account.financial.report')._get_children_by_order(self.cr, self.uid, [data['form']['account_report_id'][0]], context=data['form']['used_context'])
        for report in self.pool.get('account.financial.report').browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
            name = report.name
            code = report.code or ''
            if code:
                name += ' - (' + code + ')'
            vals = {
                'code': report.code,
                'name': name,
                'balance': report.balance * report.sign or 0.0,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type == 'sum' and 'view' or False,  # used to underline the financial report balances
            }
            if data['form']['debit_credit']:
                vals['debit'] = report.debit
                vals['credit'] = report.credit
            if data['form']['enable_filter']:
                vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
            lines.append(vals)
            account_ids = []
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if report.type == 'accounts' and report.account_ids:
                account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
            elif report.type == 'account_type' and report.account_type_ids:
                account_ids = account_obj.search(self.cr, self.uid, [('user_type', 'in', [x.id for x in report.account_type_ids])])
            if account_ids:
                for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    if report.display_detail == 'detail_flat' and account.type == 'view':
                        continue
                    flag = False
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance':  account.balance != 0 and account.balance * report.sign or account.balance,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1, 6) or 6,  # account.level + 1
                        'account_type': account.type,
                    }

                    if data['form']['debit_credit']:
                        vals['debit'] = account.debit
                        vals['credit'] = account.credit
                    if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                        flag = True
                    if data['form']['enable_filter']:
                        vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                            flag = True
                    if flag:
                        lines.append(vals)
        return lines


class wrapped_report_financial(orm.AbstractModel):
    _inherit = 'report.account.report_financial'
    _wrapped_report_class = report_financial_parser
