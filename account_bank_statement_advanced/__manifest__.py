# Copyright 2009-2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Advanced Bank Statement',
    'version': '11.0.1.5.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Advanced Bank Statement',
    'depends': [
        'account_cancel',
        'base_iban',
        'account_bank_menu',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'data/ir_sequence.xml',
        'views/assets_backend.xml',
        'views/account_bank_statement.xml',
        'views/account_bank_statement_line.xml',
        'views/account_bank_statement_line_global.xml',
        'views/statement_balance_report.xml',
        'wizard/bank_statement_balance_print.xml',
        'wizard/bank_statement_automatic_reconcile_result_view.xml',
        'report/statement_balance_report.xml',
    ],
    'installable': True,
}
