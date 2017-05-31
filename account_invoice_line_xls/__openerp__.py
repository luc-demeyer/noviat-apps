# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Invoice line search view and excel export',
    'version': '8.0.0.0.3',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'depends': ['account', 'report_xls'],
    'data': [
        'views/account_invoice_line.xml',
        'report/invoice_line_xls.xml',
    ],
    'auto_install': False,
    'installable': True,
}
