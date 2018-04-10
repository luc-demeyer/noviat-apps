# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Supplier payment with Belgian structured communication',
    'version': '10.0.0.0.1',
    'category': 'Accounting & Finance',
    'website': 'https://www.noviat.com',
    'author': 'Noviat',
    'license': 'AGPL-3',
    'data': [
        'views/account_invoice.xml',
    ],
    'depends': [
        'l10n_be_invoice_bba',
    ],
    'installable': True,
}
