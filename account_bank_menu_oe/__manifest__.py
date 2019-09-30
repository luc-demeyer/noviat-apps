# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'account_bank_menu on Odoo Enterprise',
    'summary': "Adds 'Bank and Cash' to the 'Accounting' menu",
    'version': '12.0.1.0.0',
    'author': 'Noviat',
    'category': 'Hidden',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'account_bank_menu',
        'account_accountant',
    ],
    'data': [
        'views/account_bank_menu.xml'
    ],
    'installable': True,
    'auto_install': True,
}
