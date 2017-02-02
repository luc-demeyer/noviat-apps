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

import logging

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleDiscountRule(models.Model):
    _name = 'sale.discount.rule'
    _order = 'sequence'

    sequence = fields.Integer()
    sale_discount_id = fields.Many2one(
        string='Sale Discount',
        comodel_name='sale.discount',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)
    discount_type = fields.Selection(
        selection=[
            ('perc', 'Percentage'),
            ('amnt', 'Amount')],)
    discount = fields.Float(
        help="- Type = Percentage: discount percentage."
             "- Type = Amount: discount amount per unit.")
    max_base = fields.Float('Max base amount')
    min_base = fields.Float('Min base amount')

    @api.one
    @api.constrains('discount', 'discount_type')
    def _check_sale_discount(self):
        """
        By default only discounts are supported, but you can
        adapt this method to allow also price increases.
        """
        # Check if amount is positive
        if self.discount < 0:
            raise ValidationError(_(
                "Discount Amount needs to be a positive number"))
        # Check if percentage is between 0 and 100
        elif self.discount_type == 'perc' and self.discount > 100:
            raise ValidationError(_(
                "Percentage discount must be between 0 and 100."))
