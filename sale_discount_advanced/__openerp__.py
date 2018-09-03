# -*- coding: utf-8 -*-
# Copyright (C) 2015 ICTSTUDIO (<http://www.ictstudio.eu>).
# Copyright (C) 2016-2018 Noviat nv/sa (www.noviat.com).
# Copyright (C) 2016 Onestein (http://www.onestein.eu/).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Sale Discount Advanced",
    'author': "ICTSTUDIO,Noviat,Onestein",
    'summary': """Order Amount Discounts related to Pricelists""",
    'website': "http://www.ictstudio.eu",
    'category': 'Sales',
    'version': '8.0.1.3.8',
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
