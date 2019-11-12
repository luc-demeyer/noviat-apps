# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Supplier Invoice - Check Duplicates',
    'version': '11.0.1.0.0',
    'category': 'Accounting & Finance',
    'website': 'https://www.noviat.com',
    'author': 'Noviat',
    'license': 'AGPL-3',
    'complexity': 'normal',
    'summary': 'Supplier Invoice - Check Duplicates',
    'data': [
        'views/account_invoice_views.xml',
    ],
    'depends': [
        'account_supplier_invoice_number',
    ],
    'excludes': [
        'account_invoice_supplier_ref_unique',
    ],
    'installable': True,
}
