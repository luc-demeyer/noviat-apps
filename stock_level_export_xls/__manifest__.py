# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock Level Excel export',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Warehouse Management',
    'depends': ['stock', 'report_xlsx_helper'],
    'data': [
        'wizard/wiz_export_stock_level.xml',
    ],
    'installable': True,
}
