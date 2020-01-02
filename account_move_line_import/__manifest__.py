# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Line Import',
    'version': '11.0.1.0.2',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Import Accounting Entries',
    'depends': ['account'],
    'data': [
        'views/account_move.xml',
        'wizard/import_move_line_wizard.xml',
    ],
    'installable': True,
}
