# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Journal Items Search Extension',
    'version': '10.0.0.2.1',
    'license': 'AGPL-3',
    'author': 'Noviat, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'category': 'Accounting & Finance',
    'depends': [
        'account',
        'date_range'
    ],
    'data': [
        'views/account_move_line.xml',
        'views/account_assets_backend.xml',
    ],
    'qweb': [
        'static/src/xml/account_move_line_search_extension.xml',
    ],
    'installable': True,
}
