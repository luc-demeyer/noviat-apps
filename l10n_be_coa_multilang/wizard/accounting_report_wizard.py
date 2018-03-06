# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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
