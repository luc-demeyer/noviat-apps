# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
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


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _match_payment_reference(self, coda_statement, line,
                                 coda_parsing_note):
        """
        check payment reference in bank statement line
        against payment order lines
        """
        cba = coda_statement['coda_bank_params']
        payment_reference = line['payment_reference']
        match = {}

        if payment_reference and cba.find_payment and line['amount'] < 0:
            paylines = self.env['payment.line'].search(
                [('name', '=', payment_reference)])
            if paylines:
                if len(paylines) == 1:
                    payline = paylines[0]
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
                    raise Warning(_('Error!'), err_string)

        return coda_parsing_note, match
