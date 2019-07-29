# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Journal Refund settings',
    'version': '11.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'license': 'AGPL-3',
    'depends': [
        'account_refund_menu',
    ],
    'data': [
        'views/account_journal_views.xml',
    ],
    'installable': True,
}
