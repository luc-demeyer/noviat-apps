# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models
# Copy commented lines infra to your custom module if you want
# to modify the excel template for your own specific needs.
# from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
#    import AbstractReportXlsx
# _render = AbstractReportXlsx._render

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_cost_at_date(self, res, stock_level_date):
        """
        Lookup of cost in price history table.
        The resultings Qty * Cost gives a good idea on the inventory value
        at a certain date but is not equal to the stock valuation as
        calculated by the Odoo standard stock valuation report.
        Product cost changes over time and hence we need to lookup the cost
        of each quant seperately and sum up the valuations of all quants of
        a product.

        We could implement this as follows:

        stock_hist = self.env['stock.history'].search(domain)
        whereby domain is based upon the filter options of the export wizard
        and query the resulting stock_hist to retrieve valuation per product.

        There a couple of issues though with the standard 'stock.history':
        - 'owner_id' is not supported, hence we cannot support consigned
          stocks without prior fix of the underlying report.
        - The query in the 'stock.history' report is complex resulting in
          unacceptable performance for databases with large numbers of
          products and stock moves.
          A redesign of the 'stock.history' report is required
          to make this report usable on real production level databases.
        """
        for product in self:
            # the get_history_price method has no proper multi record support
            # hence we need this for loop
            cost = product.get_history_price(self.env.context['force_company'],
                                             date=stock_level_date)
            res[product.id]['cost'] = cost

    @api.multi
    def _compute_cost_and_qty_available_at_date(self):
        lot_id = self.env.context.get('lot_id')
        owner_id = self.env.context.get('owner_id')
        package_id = self.env.context.get('package_id')
        # from_date not available via UI
        from_date = self.env.context.get('from_date')
        to_date = self.env.context.get('to_date')
        res = self._compute_quantities_dict(
            lot_id, owner_id, package_id,
            from_date=from_date, to_date=to_date
        )
        if self.env.context.get('add_cost_at_date'):
            self._get_cost_at_date(res, to_date)
        return res

    @api.model
    def _stock_level_export_xls_fields(self):
        """
        adapt list in custom module to add/drop columns or change order
        """
        return [
            'ref', 'name', 'category', 'uom', 'quantity',
            'cost_at_date', 'qty_x_cost', 'active',
        ]

    @api.model
    def _stock_level_export_xls_template(self):
        """
        Template updates, e.g.

        res = super(ProductProduct, self)._stock_level_export_xls_template()
        res.update({
            'name': {
                'header': {
                    'type': 'string',
                    'value': _('Product Name'),
                },
                'lines': {
                    'type': 'string',
                    'value': _render(
                        "line.name + (line['product'].default_code or '')"),
                },
                'width': 42,
            },
        })
        return res
        """
        return {}
