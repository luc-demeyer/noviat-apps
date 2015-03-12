Module to import CODA bank statements
=====================================


Features
--------

    * CODA v1 support.
    * CODA v2.x support.
    * Foreign Currency support.
    * Support for all data record types (0, 1, 2, 3, 4, 8, 9).
    * Parsing & logging of all Transaction Codes and Structured Format Communications.
    * Automatic Financial Journal assignment via CODA configuration parameters.
    * Support for multiple Journals per Bank Account Number.
    * Support for multiple statements from different bank accounts in a single CODA file.
    * Support for 'parsing only' CODA Bank Accounts (defined as type='info' in 
      the CODA Bank Account configuration records).
    * Multi-language CODA parsing, parsing configuration data provided for EN, NL, FR.

The machine readable CODA Files are parsed and stored in human readable format in 
CODA Bank Statements. Also Bank Statements are generated containing a subset of 
the CODA information (only those transaction lines that are required for the 
creation of the Financial Accounting records). The CODA Bank Statement is a 
'read-only' object, hence remaining a reliable representation of the original
CODA file whereas the Bank Statement will get modified as required by accounting 
business processes.

CODA Bank Accounts configured as type 'Info' will only generate CODA Bank Statements.

A removal of one object in the CODA processing results in the removal of the 
associated objects. The removal of a CODA File containing multiple Bank 
Statements will also remove those associated statements.

Reconciliation logic
--------------------

    1) The Company's Bank Account Number of the CODA statement is compared against 
       the Bank Account Number field of the Company's CODA Bank Account 
       configuration records (whereby CODA Bank Accounts defined as type='info' 
       configuration records are ignored). If this is the case an 'internal transfer' 
       transaction is generated using the Internal Transfer Account' field of the 
       CODA File Import wizard.

    2) Outgoing payments are matched with the corresponding invoice/refund via the 
       SEPA EndToEndReference field (requires **l10n_be_coda_pain** module).

    3) As a next step the 'Structured Communication' field of the CODA transaction 
       line is matched against the reference field of in- and outgoing invoices 
       (supported: Belgian Structured Communication Type). 
       In case of such a match, the transaction will be reconciled automatically 
       (full or partial).

    4) When a 'Free Format Communication' is used, a lookup is performed on 
       outstanding invoices. Reconciliation will take place when all of the following 
       conditions are met:

       - exact match of transaction amount
       - invoice/refund number (case insensitive) or structured communication is 
         present within the Free Format Communication string (substring match).

    5) If the Sale Order number is found in the 'Free Format Communication' the 
       matching will be performed with the Sale Order Invoices 
       (requires **account_coda_sale** module).

    6) When the previous steps do not result in a match, the transaction counterparty 
       is located via the Bank Account Number configured on the OpenERP Customer 
       and Supplier records.

    7) After the previous steps, the Account Mapping Rules engine determines the 
       general account to assign for the transaction.
       Also the required action is defined such as the automatic creation of 
       accounting moves with resulting account and tax case.

    8) In case none of the previous steps are successful, the transaction is created 
       with the 'Default Account for Unrecognized Movement' to allow further 
       manual processing.

In stead of a manual adjustment of the generated Bank Statements, you can also 
re-import the CODA after updating the OpenERP database with the information that 
was missing to allow automatic reconciliation.


CODA v1 support
---------------

In some cases a transaction code, transaction category or structured 
communication code has been given a new or clearer description in CODA v2.The
description provided by the CODA configuration tables is based upon the CODA v2 
specifications.
If required, you can manually adjust the descriptions via the CODA configuration menu.


Installation instructions
-------------------------

    1) This module is **NOT** compatible with the **l10n_be_coda** module.

    2) We recommend to run this module in combination with the following Noviat modules:

       - account_pain
       - l10n_be_coda_pain
       - l10n_be_coda_sale

       You can download these from the apps.odoo.com.


Assistance
----------

Contact info@noviat.com for help with the implementation of Advanced CODA processing in Odoo.

