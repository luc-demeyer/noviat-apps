# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from datetime import datetime
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import orm
from openerp.addons.account.report.account_financial_report \
    import report_account_common
import logging
_logger = logging.getLogger(__name__)


class accounting_report(orm.TransientModel):
    _inherit = 'accounting.report'

    def _build_contexts(self, cr, uid, ids, data, context=None):
        result = super(accounting_report, self)._build_contexts(
            cr, uid, ids, data, context=context)
        account_report_id = self.read(
            cr, uid, ids, ['account_report_id'], context=context
            )[0]['account_report_id'][0]
        mod_obj = self.pool.get('ir.model.data')
        module = 'l10n_be_coa_multilang'
        xml_ids = [
            'account_financial_report_BE_2_FULL',
            'account_financial_report_BE_3_FULL']
        be_legal_report_ids = []
        for xml_id in xml_ids:
            be_legal_report_ids.append(
                mod_obj.get_object_reference(cr, uid, module, xml_id)[1])
        if account_report_id in be_legal_report_ids:
            result.update({'get_children_by_sequence': True})
        return result


class report_financial_parser(report_account_common):

    def set_context(self, objects, data, ids, report_type=None):
        report_date = datetime_field.context_timestamp(
            self.cr, self.uid,
            datetime.now(), self.context
            ).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.localcontext.update({'report_date': report_date})
        super(report_financial_parser, self).set_context(
            objects, data, ids, report_type)

    def get_lines(self, data):
        lines = super(report_financial_parser, self).get_lines(data)
        for line in lines:
            if line.get('report_id'):
                # cf. https://github.com/odoo/odoo/pull/6923
                report = self.pool['account.financial.report'].browse(
                    self.cr, self.uid, line['report_id'],
                    context=data['form']['used_context'])
                code = report.code
                if code:
                    line['name'] += ' - (' + code + ')'
        return lines


class wrapped_report_financial(orm.AbstractModel):
    _inherit = 'report.account.report_financial'
    _wrapped_report_class = report_financial_parser
