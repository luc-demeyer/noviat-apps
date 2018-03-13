# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Pay Button Filter',
    'version': '8.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Account Invoice Pay Button Filter',
    'depends': ['account_voucher'],
    'data': [
        'views/account_journal_view.xml',
        'views/account_voucher_pay_invoice.xml',
    ],
    'installable': True,
}
