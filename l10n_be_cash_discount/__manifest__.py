# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Belgian Cash Discount',
    'summary': 'Cash Discount on Invoices according to Belgian Tax Rules',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat nv',
    'website': 'http://www.noviat.com',
    'category': 'Localization',
    'depends': [
        'account',
    ],
    'data': [
        'views/res_company.xml',
        'views/account_invoice.xml',
    ],
    'installable': True,
}
