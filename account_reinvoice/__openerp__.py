# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Reinvoice',
    'version': '8.0.1.1.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'Account Reinvoice',
    'depends': [
        'account',
    ],
    'data': [
        'security/account_reinvoice_security.xml',
        'security/ir.model.access.csv',
        'views/account_bank_statement.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/account_reinvoice_distribution.xml',
        'views/account_reinvoice_journal_mapping.xml',
        'views/account_reinvoice_key.xml',
        'views/account_reinvoice_line.xml',
        'views/menuitem.xml',
        'wizard/account_reinvoice_wizard.xml',
    ],
    'installable': True,
}
