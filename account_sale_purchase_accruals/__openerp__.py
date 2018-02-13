# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Sale Purchase Accruals',
    'version': '8.0.1.1.6',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'Traceable Journal Entries for Sale/Purchase/Stock process',
    'conflicts': ['account_anglo_saxon'],
    'depends': [
        'purchase_order_sale_reference',
        'account_refund_original',
    ],
    'data': [
        'data/accrual_data.xml',
        'views/account_invoice.xml',
        'views/product_category.xml',
        'views/product_template.xml',
        'views/purchase_order.xml',
        'views/res_company.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
}
