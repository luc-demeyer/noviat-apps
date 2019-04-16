# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Belgium - Import bank CODA statements',
    'version': '7.5',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'description': """
    Module to import CODA bank statements.

    Supported are CODA flat files in V2 format from Belgian bank accounts.
    - CODA v1 support.
    - CODA v2 support.
    - Foreign Currency support.
    - Support for all data record types (0, 1, 2, 3, 4, 8, 9).
    - Parsing & logging of all Transaction Codes and Structured Format Communications.
    - Automatic Financial Journal assignment via CODA configuration parameters.
    - Support for multiple Journals per Bank Account Number.
    - Support for multiple statements from different bank accounts in a single CODA file.
    - Support for 'parsing only' CODA Bank Accounts (defined as type='info' in the CODA Bank Account configuration records).
    - Multi-language CODA parsing, parsing configuration data provided for EN, NL, FR.

    The machine readable CODA Files are parsed and stored in human readable format in CODA Bank Statements.
    Also Bank Statements are generated containing a subset of the CODA information (only those transaction lines 
    that are required for the creation of the Financial Accounting records).
    The CODA Bank Statement is a 'read-only' object, hence remaining a reliable representation of the original CODA file
    whereas the Bank Statement will get modified as required by accounting business processes. 

    CODA Bank Accounts configured as type 'Info' will only generate CODA Bank Statements.

    A removal of one object in the CODA processing results in the removal of the associated objects. 
    The removal of a CODA File containing multiple Bank Statements will also remove those associated 
    statements.

    The following reconciliation logic has been implemented in the CODA processing : 
    1) The Company's Bank Account Number of the CODA statement is compared against the Bank Account Number field 
       of the Company's CODA Bank Account configuration records (whereby CODA Bank Accounts defined as type='info' configuration records are ignored). 
       If this is the case an 'internal transfer' transaction is generated using the 'Internal Transfer Account' field of the CODA File Import wizard.
    2) Outgoing payments are matched with the corresponding invoice/refund via the SEPA EndToEndReference field (requires accound_coda_pain module).
    3) As a next step the 'Structured Communication' field of the CODA transaction line is matched against 
       the reference field of in- and outgoing invoices (supported: Belgian Structured Communication Type). 
       In case of such a match, the transaction will be reconciled automatically (full or partial).
    4) When a 'Free Format Communication' is used, a lookup is performed on outstanding invoices.
       Reconciliation will take place when all of the following conditions are met :
       - exact match of transaction amount
       - invoice/refund number (case insensitive) or structured communication is present within the Free Format Communication string (substring match).
    5) If the Sale Order number is found in the 'Free Format Communication' the matching will be performed with the Sale Order Invoices (requires account_coda_sale module).
    6) When the previous steps do not result in a match, the transaction counterparty is located via the 
       Bank Account Number configured on the OpenERP Customer and Supplier records. 
    7) After the previous steps, the Account Mapping Rules engine determines the general account to assign for the transaction.
       Also the required action is defined such as the automatic creation of accounting moves with resulting account and tax case.
    8) In case none of the previous steps are successful, the transaction is created with the 'Default Account 
       for Unrecognized Movement' to allow further manual processing.

    Remark on CODA V1 support:
    In some cases a transaction code, transaction category or structured communication code has been given a new or clearer description in CODA V2.
    The description provided by the CODA configuration tables is based upon the CODA V2.2 specifications.
    If required, you can manually adjust the descriptions via the CODA configuration menu. 

    """,
    'depends': [
        'account_voucher', 
        'base_iban',
        'l10n_be_invoice_bba',
        'account_bank_statement_extensions'
    ],
    'init_xml': [
        'account_coda_trans_type.xml',
        'account_coda_trans_code.xml',
        'account_coda_trans_category.xml',
        'account_coda_comm_type.xml',
        'data/be_banks.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'res_bank_view.xml',
        'account_bank_statement_view.xml',
        'account_coda_wizard.xml',
        'account_coda_view.xml',
        'account_bank_statement_view.xml',
    ],
    'active': False,
    'installable': True,
    'license': 'AGPL-3',
    'certificate' : '001237207321716002029',
}
