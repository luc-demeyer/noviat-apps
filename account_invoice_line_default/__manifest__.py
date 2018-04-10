# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Line Defaults',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'Account Invoice Line Defaults',
    'data': [
        'views/account_invoice.xml',
        'views/res_partner.xml',
    ],
    'depends': [
        'account',
    ],
    'installable': True
}
