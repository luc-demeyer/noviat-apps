# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
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

from openerp import models, api


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        pl = False
        if vals.get('payment_reference'):
            pls = self.env['payment.line'].search(
                [('name', '=', vals['payment_reference'])])
            if len(pls) == 1:
                pl = pls[0]
        absl = super(AccountBankStatementLine, self).create(vals)
        if pl:
            pl.write({'bank_statement_line_id': absl.id})
        return absl
