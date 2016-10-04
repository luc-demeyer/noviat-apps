# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _get_procurement_action(self):
        action = False
        product = self.product_id
        if product.type in ('product', 'consu'):
            dom = [
                ('invoice_lines', '=', self.id),
                ('product_id', '=', product.id)]
            sols = self.env['sale.order.line'].search(dom)
            procs = sols.mapped('procurement_ids')
            rules = procs.mapped('rule_id')
            actions = rules.mapped('action')
            if len(actions) == 1:
                action = actions[0]
        return action
