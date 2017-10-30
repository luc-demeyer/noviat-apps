# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'ISO 20022 XML payments',
    'version': '8.0.2.1.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'ISO 20022 XML payments',
    'depends': [
        'base_iban',
        'account_payment'
    ],
    'conflicts': ['account_banking_payment_export'],
    'data': [
        'views/account_move_line.xml',
        'views/account_invoice.xml',
        'views/payment_line.xml',
        'views/payment_mode.xml',
        'views/payment_order.xml',
        'views/res_partner.xml',
        'views/res_partner_bank.xml',
        'wizard/account_pain_create.xml',
    ],
}
