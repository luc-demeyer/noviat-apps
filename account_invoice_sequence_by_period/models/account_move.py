# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @ api.multi
    def post(self):
        invoice = self._context.get('invoice', False)
        if invoice and not invoice.internal_number:
            journal = invoice.journal_id
            if journal.sequence_id:
                move = invoice.move_id
                if move:
                    period = move.period_id
                else:
                    period_id = self._context.get('period_id')
                    period = self.env['account.period'].browse(period_id)
                if period:
                    ctx = {
                        'period': period,
                        'fiscalyear_id': period.fiscalyear_id.id,
                        }
                    number = \
                        self.env['ir.sequence'].with_context(ctx).next_by_id(
                            journal.sequence_id.id)
                    invoice.internal_number = number

        return super(AccountMove, self).post()
