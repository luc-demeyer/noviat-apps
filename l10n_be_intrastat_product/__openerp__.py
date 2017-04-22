# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Intrastat Product Declaration for Belgium',
    'version': '8.0.1.0.4',
    'category': 'Intrastat',
    'license': 'AGPL-3',
    'summary': 'Base module for Intrastat Product',
    'author': 'Noviat, Odoo Community Association (OCA)',
    'depends': [
        'intrastat_product',
        'l10n_be_partner',
        ],
    'conflicts': [
        'l10n_be_intrastat',
        'report_intrastat',
        ],
    'data': [
        'security/intrastat_security.xml',
        'security/ir.model.access.csv',
        'data/intrastat_region.xml',
        'data/intrastat_transaction.xml',
        'views/account_invoice.xml',
        'views/res_company.xml',
        'views/intrastat_installer.xml',
        'views/l10n_be_intrastat_product.xml',
    ],
    'installable': True,
}
