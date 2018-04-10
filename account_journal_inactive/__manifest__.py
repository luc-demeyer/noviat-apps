# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Journal Inactive',
    'summary': 'Add active flag to Financial Journals',
    'author': 'Noviat',
    'category': 'Accounting & Finance',
    'website': 'https://www.noviat.com',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_journal.xml',
    ],
    'installable': True,
}
