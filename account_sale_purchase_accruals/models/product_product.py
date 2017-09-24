# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, _
from openerp.exceptions import except_orm, Warning as UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_purchase_pricelist_amount(self, qty, company=None):
        amount = amount_cur = 0.0
        cur = self.env['res.currency']
        dom = [('product_tmpl_id', '=', self.product_tmpl_id.id),
               ('company_id', '=', company.id)]
        main_supplier = self.env['product.supplierinfo'].search(
            dom, limit=1)
        if main_supplier:
            supplier = main_supplier.name
            pricelist = supplier.property_product_pricelist_purchase
            if pricelist:
                try:
                    price_get = pricelist.price_get(
                        self.id, qty, partner=main_supplier.id)
                except except_orm, e:
                    msg = _(
                        "Error during pricelist price_get for product '%s'."
                    ) % self.name
                    msg += '\n\n' + e.value
                    raise UserError(msg)
                if price_get:
                    amount = price_get[pricelist.id] * qty
                    if pricelist.currency_id != company.currency_id:
                        cur = pricelist.currency_id
                        amount_cur = amount
                        amount = pricelist.currency_id.compute(
                            amount, company.currency_id)
        return amount, amount_cur, cur

    def _get_expense_accrual_amount(self, qty, procurement_action='buy',
                                    company=None):
        amount = amount_cur = 0.0
        cur = self.env['res.currency']
        if procurement_action == 'buy':
            amount, amount_cur, cur = self._get_purchase_pricelist_amount(
                qty, company=company)
            if not amount:
                amount = self.standard_price * qty
        else:
            # stockable products
            amount = self.standard_price * qty
            if not amount:
                amount, amount_cur, cur = self._get_purchase_pricelist_amount(
                    qty, company=company)
        return amount, amount_cur, cur
