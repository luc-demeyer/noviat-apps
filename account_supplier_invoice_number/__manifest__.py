# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Supplier invoice number',
    'version': '12.0.1.0.1',
    'category': 'Accounting & Finance',
    'website': 'https://www.noviat.com',
    'author': 'Noviat',
    'license': 'AGPL-3',
    'data': [
        'views/account_invoice_views.xml',
    ],
    'depends': [
        'account',
    ],
    'excludes': [
        'account_invoice_supplier_ref_unique',
    ],
    'installable': True,
}
