# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Account Invoice Split',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'Split Draft Invoices',
    'data': [
        'views/account_invoice.xml',
        'wizard/account_invoice_split.xml',
        ],
    'depends': [
        'account',
        ],
    'installable': True
}
