# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 ICTSTUDIO (<http://www.ictstudio.eu>).
#    Copyright (C) 2012-2016 Noviat nv/sa (www.noviat.com).
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

from openerp import api, fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    sale_discount_ids = fields.Many2many(
        string='Sale Discounts',
        comodel_name='sale.discount',
        relation='pricelist_sale_discount_rel',
        column1='pricelist_id',
        column2='discount_id')

    @api.multi
    def _get_active_sale_discounts(self, date_order):
        self.ensure_one()
        discounts = self.env['sale.discount']
        for discount in self.sale_discount_ids:
            if discount.active and \
                    discount.check_active_date(date_order):
                discounts += discount
        return discounts
