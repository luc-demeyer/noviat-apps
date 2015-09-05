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
            aj_ids = aj_obj.search(cr, uid, domain, context=context)
            if aj_ids:
                default_journal = aj_obj.browse(
                    cr, uid, aj_ids[0], context=context)
                if default_journal.payment_date_out == 'invoice_date':
                    res['context'].update({
                        'default_period_id': inv.period_id.id,
                        'default_date': inv.date_invoice,
                        })
        else:
            domain = [('payment_method_in', '=', True)]
            aj_ids = aj_obj.search(cr, uid, domain, context=context)
            if aj_ids:
                default_journal = aj_obj.browse(
                    cr, uid, aj_ids[0], context=context)
                if default_journal.payment_date_in == 'invoice_date':
                    res['context'].update({
                        'default_period_id': inv.period_id.id,
                        'default_date': inv.date_invoice,
                        })

        if not aj_ids:
            raise Warning(
                _("No Payment Methods defined for "
                  "the 'Register Payment' function"))

        res['name'] = _("Register Payment")
        res['context'].update({
            'payment_journal_ids': aj_ids,
            'default_journal_id': aj_ids[0],
            'account_invoice_pay_filter': True,
            })
        return res
