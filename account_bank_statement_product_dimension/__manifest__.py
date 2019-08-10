# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Add product field to the Bank Statement reconciliation',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'depends': [
        'account',
    ],
    'data': [
        'views/assets_backend.xml',
        'views/account_move_views.xml',
        'views/account_move_line_views.xml',
    ],
    'qweb': [
        'static/src/xml/account_reconciliation.xml',
    ],
    'installable': True,
}
