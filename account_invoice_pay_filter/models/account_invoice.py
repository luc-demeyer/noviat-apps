# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, _
from openerp.exceptions import Warning


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_pay_customer(
            cr, uid, ids, context=context)
        if not res:
            return res

        aj_obj = self.pool['account.journal']
        inv = self.browse(cr, uid, ids[0])
        if inv.type in ('in_invoice', 'out_refund'):
            domain = [('payment_method_out', '=', True)]
        else:
            domain = [('payment_method_in', '=', True)]
        aj_ids = aj_obj.search(cr, uid, domain, context=context)
        if not aj_ids:
            raise Warning(
                _("No Payment Methods defined for "
                  "the 'Register Payment' function"))

        res['name'] = _("Register Payment")
        res['context'].update({
            'payment_journal_ids': aj_ids,
            'default_journal_id': aj_ids[0],
            'account_invoice_pay_filter': True,
            'invoice_date': inv.date_invoice,
            'invoice_period_id': inv.period_id.id,
        })
        return res
