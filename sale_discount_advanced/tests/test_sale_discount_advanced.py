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

from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError


class TestSaleDiscountAdvanced(TransactionCase):

    def setUp(self):
        super(TestSaleDiscountAdvanced, self).setUp()
        self.so_obj = self.env['sale.order']
        self.sd_obj = self.env['sale.discount']
        self.sdl_obj = self.env['sale.discount.rule']
        self.partner_id = self.ref('base.res_partner_2')
        self.pricelist_order_id = self.ref(
            'sale_discount_advanced.pricelist_discount_on_sale_order')
        self.pricelist_line_id = self.ref(
            'sale_discount_advanced.pricelist_discount_on_sale_order_line')

    def test_lower_min_base_threshold(self):
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_order_id,
            'order_line': [
                (0, 0, {
                    'product_id': self.ref('product.product_product_24'),
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 950
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 950,
                          "Total amount should be 950.00")
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_line_id,
            'order_line': [
                (0, 0, {
                    'product_id': self.ref('product.product_product_24'),
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 950
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 950,
                          "Total amount should be 950.00")

    def test_higher_min_base_threshold(self):
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_order_id,
            'order_line': [
                (0, 0, {
                    'product_id': self.ref('product.product_product_24'),
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 1000
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 750,
                          "Total amount should be 750.00")
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_line_id,
            'order_line': [
                (0, 0, {
                    'product_id': self.ref('product.product_product_24'),
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 1000
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 900,
                          "Total amount should be 900.00")

    def test_next_min_base_threshold(self):
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_order_id,
            'order_line': [
                (0, 0, {
                    'product_id': self.ref('product.product_product_24'),
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 3000
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 1500,
                          "Total amount should be 1500.00")
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_line_id,
            'order_line': [
                (0, 0, {
                    'product_id': self.ref('product.product_product_24'),
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 3000
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 2900,
                          "Total amount should be 2900.00")

    def test_discount_out_of_date_range(self):
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2015-02-01 08:30:00',
            'pricelist_id': self.pricelist_order_id,
            'order_line': [
                (0, 0, {
                    'product_id': self.ref('product.product_product_24'),
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 3000
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 3000,
                          "Total amount should be 3000.00")

    def test_no_product(self):
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_order_id,
            'order_line': [
                (0, 0, {
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 3000
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 3000,
                          "Total amount should be 3000.00")

    def test_excluded_products(self):
        excluded_by_product = self.ref('product.product_product_consultant')
        excluded_by_category = self.ref('product.product_product_11')
        so = self.so_obj.create({
            'partner_id': self.partner_id,
            'date_order': '2016-02-01 08:30:00',
            'pricelist_id': self.pricelist_line_id,
            'order_line': [
                (0, 0, {
                    'product_id': excluded_by_category,
                    'name': 'Line 1',
                    'product_uom_qty': 1,
                    'price_unit': 3000
                }),
                (0, 0, {
                    'product_id': excluded_by_product,
                    'name': 'Line 2',
                    'product_uom_qty': 1,
                    'price_unit': 3000
                })
            ]
        })
        so.button_dummy()
        self.assertEquals(so.amount_total, 6000,
                          "Total amount should be 6000.00")

    def test_constraints_sale_discount(self):
        with self.assertRaises(ValidationError):
            self.sd_obj.create({
                'name': 'Discount',
                'start_date': '2013-01-01',
                'end_date': '2012-01-01'
            })

    def test_constraints_sale_discount_line(self):
        sd = self.sd_obj.create({
            'name': 'Discount',
            'start_date': '2012-01-01',
            'end_date': '2013-01-01'
        })
        # Test lower max
        with self.assertRaises(ValidationError):
            self.sdl_obj.create({
                'sale_discount_id': sd.id,
                'discount_type': 'perc',
                'min_base': 200,
                'max_base': 100,
                'discount': 25
            })
        # Test < 0 discount
        with self.assertRaises(ValidationError):
            self.sdl_obj.create({
                'sale_discount_id': sd.id,
                'discount_type': 'amnt',
                'min_base': 100,
                'max_base': 200,
                'discount': -1
            })
        # Test > 100% discount
        with self.assertRaises(ValidationError):
            self.sdl_obj.create({
                'sale_discount_id': sd.id,
                'discount_type': 'perc',
                'min_base': 100,
                'max_base': 200,
                'discount': 110
            })
        # Test < 0 min_base
        with self.assertRaises(ValidationError):
            self.sdl_obj.create({
                'sale_discount_id': sd.id,
                'discount_type': 'perc',
                'min_base': -1,
                'max_base': 200,
                'discount': 25
            })
