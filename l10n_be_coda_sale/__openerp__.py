# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'CODA Import - Sale Order Matching',
    'version': '8.0.2.0.2',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'CODA Import - Sale Order Matching',
    'website': 'http://www.noviat.com',
    'depends': [
        'l10n_be_coda_advanced',
        'sale',
    ],
    'data': [
        'views/coda_bank_account.xml',
    ],
    'installable': True,
}
