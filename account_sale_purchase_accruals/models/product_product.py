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


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_expense_accrual_amount(self, qty, procurement_action='buy',
                                    company_id=None):
        amount = 0.0
        if procurement_action == 'buy':
            dom = [('product_tmpl_id', '=', self.product_tmpl_id.id),
                   ('company_id', '=', company_id)]
            main_supplier = self.env['product.supplierinfo'].search(
                dom, limit=1)
            if main_supplier:
                supplier = main_supplier.name
                pricelist = supplier.property_product_pricelist_purchase
                if pricelist:
                    price_get = pricelist.price_get(
                        self.id, qty, partner=main_supplier.id)
                    if price_get:
                        amount = price_get[pricelist.id] * qty
        if not amount:
            amount = self.standard_price * qty
        return amount
