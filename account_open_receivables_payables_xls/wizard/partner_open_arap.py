# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010-2015 Noviat nv/sa (www.noviat.com).
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

import time
from openerp.osv import orm, fields
import logging
_logger = logging.getLogger(__name__)


class wiz_partner_open_arap_period(orm.TransientModel):
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
