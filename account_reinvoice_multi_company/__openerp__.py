# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Reinvoice Multi-Company',
    'version': '8.0.1.0.6',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'Account Reinvoice Multi-Company',
    'depends': [
        'account_reinvoice',
    ],
    'data': [
        'security/account_reinvoice_multi_company.xml',
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/account_reinvoice_journal_mapping_multi_company.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
}
