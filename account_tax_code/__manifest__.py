# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'account tax code',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': """
        Add 'code' field to taxes
    """,
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
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
