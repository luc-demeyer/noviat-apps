# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'account tax code',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': """
        Add 'code' field to taxes
    """,
    'author': 'Noviat',
    'website': 'https://www.noviat.com',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_invoice.xml',
        'views/account_invoice_tax.xml',
        'views/account_tax.xml',
        'views/account_tax_template.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
