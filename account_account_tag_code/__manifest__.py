# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'account tag code',
    'version': '11.0.1.0.1',
    'category': 'Accounting & Finance',
    'summary': """
        Add 'code' field to account tags
    """,
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_account_tag.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
