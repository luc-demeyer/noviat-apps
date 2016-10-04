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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Account Sale Purchase Accruals',
    'version': '8.0.1.0.0',
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
