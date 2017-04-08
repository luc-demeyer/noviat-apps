# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Analytic Dimension Policy',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Accounting & Finance',
    'depends': ['account'],
    'data': [
        'views/account_account_type.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'views/account_invoice_tax.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/assets_backend.xml',
        ],
    'installable': True,
}
