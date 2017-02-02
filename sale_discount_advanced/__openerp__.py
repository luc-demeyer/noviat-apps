# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 ICTSTUDIO (<http://www.ictstudio.eu>).
#    Copyright (C) 2016 Noviat nv/sa (www.noviat.com).
#    Copyright (C) 2016 Onestein (http://www.onestein.eu/).
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

{
    'name': "Sale Discount Advanced",
    'author': "ICTSTUDIO,Noviat,Onestein",
    'summary': """Order Amount Discounts related to Pricelists""",
    'website': "http://www.ictstudio.eu",
    'category': 'Sales',
    'version': '8.0.1.3.4',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_view.xml',
        'views/sale_discount_view.xml',
        'views/sale_order_view.xml',
    ],
    'demo': [
        'demo/product_pricelist_demo.xml',
        'demo/product_pricelist_version_demo.xml',
        'demo/product_pricelist_item_demo.xml',
        'demo/sale_discount_demo.xml',
        'demo/sale_discount_rule_demo.xml',
    ]
}
