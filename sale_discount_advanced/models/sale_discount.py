# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 ICTSTUDIO (<http://www.ictstudio.eu>).
#    Copyright (C) 2016 Noviat nv/sa (www.noviat.com).
#    Copyright (C) 2016 Onestein (http://www.onestein.eu).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class SaleDiscount(models.Model):
    _name = 'sale.discount'
    _order = 'sequence'

    sequence = fields.Integer()
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)
    name = fields.Char(
        string='Discount',
        required=True)
    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')
    active = fields.Boolean(
        string='Discount active',
        default=lambda self: self._default_active())
    discount_base = fields.Selection(
        selection=lambda self: self._selection_discount_base(),
        string='Discount Base on',
        required=True,
        default='sale_order',
        help="Base the discount on ")
    pricelist_ids = fields.Many2many(
        comodel_name='product.pricelist',
        relation='pricelist_sale_discount_rel',
        column1='discount_id',
        column2='pricelist_id')
    rule_ids = fields.One2many(
        comodel_name='sale.discount.rule',
        inverse_name='sale_discount_id',
        string='Discount Rules')
    excluded_product_category_ids = fields.Many2many(
        comodel_name='product.category',
        string='Excluded Product Categories',
        help="Products in these categories will by default be excluded "
             "from this discount.")
    excluded_product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Excluded Products',
        help="These products will by default be excluded "
             "from this discount.")

    @api.multi
    def unlink(self):
        if any(self.env['sale.order.line'].search(
                [('sale_discount_ids', 'in', self.ids)], limit=1)):
            raise UserError(_(
                'You cannot delete a discount which is used in a Sale Order!'))
        return super(SaleDiscount, self).unlink()

    @api.model
    def _default_active(self):
        return True

    @api.model
    def _selection_discount_base(self):
        """
        Separate method to allow the removal of an option
        via inherit.
        """
        selection = [
            ('sale_order', 'Base discount on Order amount'),
            ('sale_line', 'Base discount on Line amount')]
        return selection

    def check_active_date(self, check_date=None):
        if not check_date:
            check_date = fields.Datetime.now()
        if self.start_date and self.end_date \
                and (check_date >= self.start_date
                     and check_date < self.end_date):
            return True
        if self.start_date and not self.end_date \
                and (check_date >= self.start_date):
            return True
        if not self.start_date and self.end_date \
                and (check_date < self.end_date):
            return True
        elif not self.start_date or not self.end_date:
            return True
        else:
            return False

    def _calculate_discount(self, price_unit, qty):
        base = qty * price_unit
        disc_amt = 0.0
        disc_pct = 0.0
        for rule in self.rule_ids:
            if rule.min_base > 0 and rule.min_base > base:
                continue
            if rule.max_base > 0 and rule.max_base < base:
                continue

            if rule.discount_type == 'perc':
                disc_amt = base * rule.discount / 100
                disc_pct = rule.discount
            else:
                disc_amt = min(rule.discount * qty, base)
                disc_pct = disc_amt / base
        return disc_amt, disc_pct

    def _get_excluded_products(self):
        products = self.excluded_product_ids

        def get_children_recursive(categ):
            res = categ
            for child in categ.child_id:
                res += get_children_recursive(child)
            return res

        categs = self.env['product.category']
        for categ in self.excluded_product_category_ids:
            categs += get_children_recursive(categ)
        products += self.env['product.product'].search(
            [('categ_id', 'in', categs._ids)])

        return products
