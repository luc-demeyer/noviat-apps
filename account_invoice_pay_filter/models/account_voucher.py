# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
                    'date': context.get('invoice_date'),
                    'period_id': context.get('invoice_period_id'),
                })
            else:
                res['value'].update({
                    'date': time.strftime('%Y-%m-%d'),
                })
        return res
