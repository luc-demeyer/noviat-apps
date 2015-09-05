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

from openerp import models
from lxml import etree
import time


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(account_voucher, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type,
            context=context, toolbar=toolbar, submenu=False)
        if not context:
            context = {}

        if view_type == 'form' and context.get('payment_journal_ids'):
            payment_journal_ids = context['payment_journal_ids']
            view_obj = etree.XML(res['arch'])
            j_obj = view_obj.xpath("//field[@name='journal_id']")
            for el in j_obj:
                domain = [('id', 'in', payment_journal_ids)]
                el.set('domain', str(domain))
            res['arch'] = etree.tostring(view_obj)
        return res

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id,
                         partner_id, date, amount, ttype, company_id,
                         context=None):
        res = super(account_voucher, self).onchange_journal(
            cr, uid, ids, journal_id, line_ids, tax_id, partner_id,
            date, amount, ttype, company_id, context=context) or {}
        if context is None:
            context = {}
        if context.get('account_invoice_pay_filter'):
            if not res:
                res['value'] = {}
            journal = self.pool['account.journal'].browse(
                cr, uid, journal_id, context=context)
            policy = context['invoice_type'] in ('in_invoice', 'out_refund') \
                and journal.payment_date_out \
                or journal.payment_date_in
            if policy == 'invoice_date':
                res['value'].update({
                    'date': context.get('default_date'),
                    'period_id': context.get('default_period_id'),
                    })
            else:
                res['value'].update({
                    'date': time.strftime('%Y-%m-%d'),
                    })
        return res
