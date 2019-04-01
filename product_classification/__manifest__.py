# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Product Classification',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Product Management',
    'depends': [
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_classification.xml',
        'views/product_classification.xml',
        'views/product_template.xml',
    ],
    'installable': True,
}
