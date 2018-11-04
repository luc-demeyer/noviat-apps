# -*- coding: utf-8 -*-
# Copyright 2015 Onestein BV (www.onestein.eu).
# Copyright 2018 Noviat (www.noviat.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Order Purchase Reference',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Onestein, Noviat',
    'category': 'Sale',
    'complexity': 'normal',
    'summary': 'Sale Order Purchase Reference',
    'depends': [
        'purchase_order_sale_reference',
    ],
    'data': [
        'views/sale_order.xml',
        'views/purchase_order.xml',
    ],
}
