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

from openerp import models


class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    def create(self, cr, uid, vals, context=None):
        if vals.get('payment_line_id'):
            pl_id = vals['payment_line_id']
            del vals['payment_line_id']
        else:
            pl_id = False
        absl_id = super(account_bank_statement_line, self).create(
            cr, uid, vals, context=context)
        if pl_id:
            self.pool['payment.line'].write(
                cr, uid, [pl_id],
                {'bank_statement_line_id': absl_id}, context=context)
        return absl_id
