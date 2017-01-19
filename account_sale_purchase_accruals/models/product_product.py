# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_purchase_pricelist_amount(self, qty, company_id=None):
        amount = 0.0
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
        return amount

    def _get_expense_accrual_amount(self, qty, procurement_action='buy',
                                    company_id=None):
        if procurement_action == 'buy':
            amount = self._get_purchase_pricelist_amount(
                qty, company_id=company_id)
            if not amount:
                amount = self.standard_price * qty
        else:
            # stockable products
            amount = self.standard_price * qty
            if not amount:
                amount = self._get_purchase_pricelist_amount(
                    qty, company_id=company_id)
        return amount
