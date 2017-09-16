# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Advanced Bank Statement',
    'version': '8.0.3.1.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Advanced Bank Statement',
    'depends': [
        'account',
        'account_cancel',
        'base_iban',
        'web_sheet_full_width_selective',
    ],
    'conflicts': ['account_bank_statement_extensions'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'data/data.xml',
        'views/account_bank_statement.xml',
        'views/account_bank_statement_line.xml',
        'views/account_bank_statement_line_global.xml',
        'views/account_move.xml',
        'views/report_layout.xml',
        'views/report_statement_balances.xml',
        'views/account.xml',
        'wizard/bank_statement_balance_print.xml',
        'wizard/bank_statement_automatic_reconcile_result_view.xml',
        'report/reports.xml',
    ],
    'installable': True,
}
