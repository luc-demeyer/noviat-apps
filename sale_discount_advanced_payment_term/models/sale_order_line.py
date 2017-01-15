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

import logging

from openerp import api, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_sale_discount_ids(self, cr, uid, pricelist_id,
                               date_order, product_id, context=None):
        res = super(SaleOrderLine, self)._get_sale_discount_ids(
            cr, uid, pricelist_id, date_order, product_id, context=context)
        if context is None:
            context = {}
        discounts = self.env['sale.discount']
        if context.get('payment_term_id'):
            self.env = api.Environment(cr, uid, context)
            payterm = self.env['account.payment.term'].browse(
                context['payment_term_id'])
            for discount in payterm._get_active_sale_discounts(date_order):
                if product_id not in discount._get_excluded_products()._ids:
                    discounts += discount
        return res + discounts._ids

    def _get_sale_discounts(self):
        res = super(SaleOrderLine, self)._get_sale_discounts()
        discounts = self.env['sale.discount']
        payterm = self.order_id.payment_term
        if payterm:
            active_discounts = payterm._get_active_sale_discounts(
                self.order_id.date_order)
            for discount in active_discounts:
                if self.product_id not in discount._get_excluded_products():
                    discounts += discount
        return res + discounts
