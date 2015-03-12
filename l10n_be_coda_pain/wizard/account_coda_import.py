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

from openerp.osv import orm
from openerp.tools.translate import _


class account_coda_import(orm.TransientModel):
    _inherit = 'account.coda.import'

    def _st_line_hook(self, cr, uid, coda_bank_params, line, st_line_vals, context=None):
        if line.get('payment_line_id'):
            st_line_vals['payment_line_id'] = line['payment_line_id']
        return super(account_coda_import, self)._st_line_hook(cr, uid, coda_bank_params, line, st_line_vals, context=context)

    def _match_payment_reference(self, cr, uid, st_line, coda_parsing_note, coda_statement, context=None):
        """ check payment reference in bank statement line against payment order lines """
        payment_line_obj = self.pool.get('payment.line')
        coda_bank_params = coda_statement['coda_bank_params']
        find_payment = coda_bank_params['find_payment']
        match={}

        payment_reference = st_line['payment_reference']
        if payment_reference and find_payment and st_line['amount'] < 0:
            payline_ids = payment_line_obj and payment_line_obj.search(cr, uid, [('name', '=', payment_reference)])
            if payline_ids:
                if len(payline_ids) == 1:
                    payline = payment_line_obj.browse(cr, uid, payline_ids[0], context=context)
                    match['payment_line_id'] = payline.id
                    st_line['payment_line_id'] = payline.id
                    st_line['partner_id'] = payline.partner_id.id
                    if payline.move_line_id:
                        st_line['reconcile'] = payline.move_line_id.id
                        st_line['account_id'] = payline.move_line_id.account_id.id
                        st_line['type'] = payline.move_line_id.account_id.type == 'receivable' and 'customer' or 'supplier'
                else:
                    err_string = _('\nThe CODA parsing detected a payment reference ambiguity while processing movement data record 2.3, seq nr %s!'    \
                        '\nPlease check your Payment Gateway configuration or contact your OpenERP support channel.') % line[2:10]
                    err_code = 'R2007'
                    if self.batch:
                        return (err_code, err_string)
                    raise orm.except_orm(_('Error!'), err_string)

        return st_line, coda_parsing_note, match

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: