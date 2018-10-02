# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Intrastat Product Declaration for Belgium',
    'version': '10.0.1.0.1',
    'category': 'Intrastat',
    'license': 'AGPL-3',
    'summary': 'Intrastat Product Declaration for Belgium',
    'author': 'Noviat',
    'depends': [
        'intrastat_product',
        'stock_picking_invoice_link',
        'l10n_be_partner_kbo_bce',
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
        'views/account_config_settings.xml',
        'views/account_invoice.xml',
        'views/intrastat_installer.xml',
        'views/l10n_be_intrastat_product.xml',
    ],
    'installable': True,
}
