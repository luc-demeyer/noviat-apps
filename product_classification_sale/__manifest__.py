# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Product Classification',
    'version': '11.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Product Management',
    'depends': [
        'product_classification',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': True,
}
