# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2010-now Noviat nv/sa (www.noviat.com).
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
from openerp.exceptions import except_orm


class account_coda_import(models.TransientModel):
    _inherit = 'account.coda.import'

    def _match_payment_reference(self, cr, uid, coda_statement, line,
                                 coda_parsing_note, context=None):
        """
        check payment reference in bank statement line
        against payment order lines
        """
        payment_line_obj = self.pool['payment.line']
        cba = coda_statement['coda_bank_params']
        find_payment = cba['find_payment']
        payment_reference = line['payment_reference']
        match = {}

        if payment_reference and find_payment and line['amount'] < 0:
            payline_ids = payment_line_obj.search(
                cr, uid, [('name', '=', payment_reference)])
            if payline_ids:
                if len(payline_ids) == 1:
                    payline = payment_line_obj.browse(
                        cr, uid, payline_ids[0], context=context)
                    match['payment_line_id'] = payline.id
                    line['payment_line_id'] = payline.id
                    line['partner_id'] = payline.partner_id.id
                    if payline.move_line_id:
                        line['reconcile'] = payline.move_line_id.id
                else:
                    err_string = _(
                        "\nThe CODA parsing detected a "
                        "payment reference ambiguity while processing "
                        "movement data record 2.3, seq nr %s!"
                        "\nPlease check your Payment Gateway configuration "
                        "or contact your Odoo support channel."
                        ) % line[2:10]
                    err_code = 'R2007'
                    if self._batch:
                        return (err_code, err_string)
                    raise except_orm(_('Error!'), err_string)

        return coda_parsing_note, match
