# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Bank Menu',
    'summary': "Adds 'Bank and Cash' to the 'Accounting' menu",
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'website': 'https://github.com/OCA/account-financial-tools',
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'account',
    ],
    'data': [
        'views/account_bank_menu.xml'
    ],
}
