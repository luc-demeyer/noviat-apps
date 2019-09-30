# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Belgium - Advanced CODA statements Import',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'Belgium - Advanced CODA statements Import',
    'depends': [
        'base_iban',
        'l10n_be_invoice_bba_customer_supplier',
        'l10n_be_partner_bank',
        'account_bank_statement_advanced',
        'account_bank_statement_import_helper',
    ],
    'excludes': [
        'l10n_be_coda',
        'l10n_be_invoice_bba'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'data/account_coda_trans_type.xml',
        'data/account_coda_trans_code.xml',
        'data/account_coda_trans_category.xml',
        'data/account_coda_comm_type.xml',
        'views/account_bank_statement_views.xml',
        'views/account_bank_statement_line_views.xml',
        'views/account_coda_views.xml',
        'views/account_coda_comm_type_views.xml',
        'views/account_coda_trans_category_views.xml',
        'views/account_coda_trans_code_views.xml',
        'views/account_coda_trans_type_views.xml',
        'views/coda_bank_account_views.xml',
        'views/menuitem.xml',
        'wizard/account_coda_import.xml',
    ],
    'installable': True,
}
