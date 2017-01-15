# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#    Copyright (c) 2016 Onestein (www.onestein.eu).
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
    'name': 'Sale Discount on Payment Terms',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat,Onestein',
    'website': 'http://www.noviat.com',
    'category': 'Sales',
    'depends': ['sale_discount_advanced'],
    'data': [
        'views/account_payment_term.xml',
        'views/sale_discount.xml',
        'views/sale_order.xml',
    ],
    'demo': [
        'demo/sale_discount_demo.xml'
    ],
    'installable': True,
}
