# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Invoice Line Import',
    'version': '8.0.1.0.3',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Import Invoice Lines',
    'depends': ['account'],
    'data': [
        'views/account_invoice.xml',
        'wizard/import_invoice_line_wizard.xml',
    ],
    'installable': True,
}
