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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp import api, models
from openerp.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_cost_at_date(self, product, dt):
        """
        return cost at date for cost_method != 'real'
        """
        company_id = self._context.get('force_company') \
            or self.env.user.company_id.id
        cost = self.env['product.template'].get_history_price(
            product.product_tmpl_id.id, company_id, date=dt)
        return cost

    @api.multi
    def _compute_cost_and_qty_available_at_date(self):
        # logic based on _product_available method from standard addons
        context = self._context
        res = {}
        if not context.get('to_date'):
            for product in self:
                res[product.id] = (product.qty_available,
                                   product.standard_price)
            return res

        domain_move_in, domain_move_out = [], []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = \
            self._get_domain_locations()
        domain_dates = self._get_domain_dates()
        domain_move_in += domain_dates
        domain_move_in += [('state', '=', 'done')]
        domain_move_out += domain_dates
        domain_move_out += [('state', '=', 'done')]

        if context.get('owner_id'):
            owner_domain = ('restrict_partner_id', '=', context['owner_id'])
            domain_move_in.append(owner_domain)
            domain_move_out.append(owner_domain)

        domain_move_in += domain_move_in_loc
        domain_move_out += domain_move_out_loc

        domain_products = [('product_id', 'in', self._ids)]
        moves_in = self.env['stock.move'].read_group(
            domain_move_in + domain_products, ['product_id', 'product_qty'],
            ['product_id'])
        moves_out = self.env['stock.move'].read_group(
            domain_move_out + domain_products, ['product_id', 'product_qty'],
            ['product_id'])

        moves_in = dict(
            map(lambda x: (x['product_id'][0], x['product_qty']), moves_in))
        moves_out = dict(
            map(lambda x: (x['product_id'][0], x['product_qty']), moves_out))

        for product in self:
            in_qty = float_round(moves_in.get(product.id, 0.0),
                                 precision_rounding=product.uom_id.rounding)
            out_qty = float_round(moves_out.get(product.id, 0.0),
                                  precision_rounding=product.uom_id.rounding)
            qty_available_at_date = in_qty - out_qty

            cost = 0.0
            # skip calculation when 0.0 qty
            if qty_available_at_date:
                if product.cost_method != 'real':
                    cost = self._get_cost_at_date(product, context['to_date'])
                if not cost:
                    # retrieve cost from stock_history view
                    # this should only be needed for cost_method = real
                    # but we also fall back to this view for cases
                    # where the product_price_history table is not correct,
                    # e.g. incorrectly migrated databases
                    domain_product = [('product_id', '=', product.id)]
                    if moves_in:
                        in_ids = self.pool['stock.move'].search(
                            self._cr, self._uid,
                            domain_move_in + domain_product, context=context)
                    else:
                        in_ids = []
                    if moves_out:
                        out_ids = self.pool['stock.move'].search(
                            self._cr, self._uid,
                            domain_move_out + domain_product, context=context)
                    else:
                        out_ids = []
                    move_ids = in_ids + out_ids
                    if move_ids:
                        self._cr.execute(
                            "SELECT quantity, price_unit_on_quant "
                            "FROM stock_history WHERE move_id in %s",
                            (tuple(move_ids),))
                        histories = self._cr.dictfetchall()
                        sum = 0.0
                        for h in histories:
                            sum += h['quantity'] * h['price_unit_on_quant']
                        cost = sum / qty_available_at_date
            res[product.id] = (qty_available_at_date, cost)
        return res

    @api.model
    def _stock_level_export_xls_fields(self):
        """
        adapt list in custom module to add/drop columns or change order
        """
        return [
            # Inventory fields
            'ref', 'name', 'category', 'uom', 'quantity',
            # Stock Valuation fields
            'cost', 'stock_value',
        ]

    @api.model
    def stock_level_export_xls_template(self):
        """
        Template updates, e.g.

        res = super(ProductProduct, self).stock_level_export_xls_template()
        res.update({
            'name': {
                'header': [1, 42, 'text', _render("_('Name')")],
                'products': [1, 0, 'text', _render("product.name or ''")],
                'totals': [1, 0, 'text', None]},
        })
        return res
        """
        return {}
