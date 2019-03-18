.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================================
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
    * Multi-language CODA parsing, parsing configuration data provided for EN, NL, FR.
    * Support for 'globalisation' of transactions (performed by the customer or the bank).
      A globalised transaction is presented in the bank statement with its global level (or levels)
      showing the total amount. Also the individual transactions are available for further bank statement
      processing.
    * All information supplied in the CODA file is presented in the bank statement.
      This includes also non-transactional data such as 'free communication' supplied
      by the bank via the CODA File.
      Transaction specific information can be found in the 'Notes' field of the transaction.
      Generic communication is available via the 'CODA Notes' field of the Bank Statement.

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

    6) If no matching accounting entry is found via the originating business transactions
       (Payment Order, Invoice, Sales Order) a lookup is performed directly on
       the accounting entries.
       Reconciliation will take place when all of the following
       conditions are met:

       - exact match of transaction amount
       - the payment communication needs to be a subset of the accounting entry 'name' field

    7) When the previous steps do not result in a match, the transaction counterparty
       is located via the Bank Account Number configured on the OpenERP Customer
       and Supplier records.

    8) Partner records are updated automatically with the partner's bank account information
       supplied in the CODA file.

    9) After the previous steps, the Account Mapping Rules engine determines the
       general account to assign for the transaction.
       Also the required action is defined such as the automatic creation of
       accounting moves with resulting account and tax case.

CODA v1 support
---------------

In some cases a transaction code, transaction category or structured
communication code has been given a new or clearer description in CODA v2.
The description provided by the CODA configuration tables is based upon the
CODA v2 specifications.
If required, you can manually adjust the descriptions via the CODA configuration menu.

Installation instructions
-------------------------

    1) This module is **NOT** compatible with the **l10n_be_coda** module.

    2) We recommend to run this module in combination with the following Noviat modules:

       - l10n_be_coda_pain
       - l10n_be_coda_sale

       You can download these from the apps.odoo.com.


Assistance
----------

Contact info@noviat.com for help with the implementation of Advanced CODA processing in Odoo.
