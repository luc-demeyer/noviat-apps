# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from openerp.osv import orm, fields
import logging
_logger = logging.getLogger(__name__)


class WizPartnerOpenArapPeriod(orm.TransientModel):
    _name = 'wiz.partner.open.arap.period'
    _description = 'Print Open Receivables/Payables by Period'

    def _get_period(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        periods = self.pool.get('account.period').search(
            cr, uid,
            [('date_start', '<=', now), ('date_stop', '>=', now)], limit=1)
        return periods and periods[0] or False

    def _get_company(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(
            cr, uid, 'account.account', context=context)

    _columns = {
        'period_id': fields.many2one(
            'account.period', 'Period', required=True),
        'target_move': fields.selection(
            [('posted', 'All Posted Entries'),
             ('all', 'All Entries')],
            'Target Moves', required=True),
        'result_selection': fields.selection(
            [('customer', 'Receivable Accounts'),
             ('supplier', 'Payable Accounts'),
             ('customer_supplier', 'Receivable and Payable Accounts')],
            "Partner's", required=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True)
    }
    _defaults = {
        'period_id': _get_period,
        'target_move': 'posted',
        'result_selection': 'customer',
        'company_id': _get_company,
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        period_id = data['period_id'][0]
        company_id = data['company_id'][0]
        data.update({
            'period_id': period_id,
            'company_id': company_id,
        })
        if context.get('xls_export'):
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'account.partner.open.arap.period.xls',
                    'datas': data}
        else:
            context['landscape'] = True
            return self.pool['report'].get_action(
                cr, uid, [],
                'account_open_receivables_payables_xls.report_open_arap',
                data=data, context=context)

    def xls_export(self, cr, uid, ids, context=None):
        return self.print_report(cr, uid, ids, context=context)
