# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'account tag code',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': """
        Add 'code' field to account tags
    """,
    'author': 'Noviat',
    'website': 'https://www.noviat.com',
    'depends': [
        'account_tag_menu',
    ],
    'data': [
        'views/account_account_tag_views.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
