# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Belgium - KBO/BCE numbers',
    'category': 'Localization',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'website': 'https://odoo-community.org/',
    'depends': [
        'partner_identification',
        'base_vat_sanitized',
    ],
    'data': [
        'data/res_partner_id_category.xml',
        'views/res_partner.xml',
    ],
    'demo': [
        'demo/res_partner.xml',
    ],
    'installable': True,
}
