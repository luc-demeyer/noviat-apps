# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'CODA Reinvoice Key',
    'version': '8.0.2.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'depends': [
        'l10n_be_coda_advanced',
        'account_reinvoice',
    ],
    'data': [
        'views/coda_bank_account.xml',
    ],
    'installable': True,
    'auto_install': True,
}
