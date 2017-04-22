# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Belgium - Partner Model customizations',
    'version': '8.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Localization',
    'summary': 'Belgium - Partner Model customisations',
    'depends': [
        'base_vat',
        'base_iban',
    ],
    'data': [
        'data/be_base_data.xml',
        'data/be_banks.xml',
        'views/res_bank.xml',
        'views/res_partner.xml',
    ],
    'demo': [
        'demo/res_partner.xml',
    ],
    'installable': True,
}
