# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'l10n_be_coa_multilang on Odoo Enterprise',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Hidden',
    'depends': [
        'account_reports',
        'l10n_be_coa_multilang',
    ],
    'data': [
        'views/account_financial_report.xml',
    ],
    'installable': True,
    'auto_install': True,
}
