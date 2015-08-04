ISO 20022 XML payment files
===========================

Module to generate Customer Credit Transfer Initiation message ISO 20022 XML - pain.001.001.03.
Both SEPA and non-SEPA payments are supported.

Other features:
---------------
- The module prohibits the removal of a confirmed Payment Order.
  Such a removal is still possible via the 'Undo Payment' button
  available to users of the 'Accounting / Manager' group.
- Support for customer invoices as well as supplier credit notes.
- Invoices with the 'Supplier Direct Debit' flag set will be excluded
  from the 'Select Invoices to Pay' filter
- The 'Supplier Invoice Number' field is automatically copied
  to the Communication (for type 'Free Communication')
  so that the Supplier Invoicing Number will be used by default as the payment communication
  when sending Payment Orders to the bank.

Features targeted for the Belgian market (cf. febelfin guidelines):

* creditor account identified by IBAN (without BIC) for BE IBAN accounts
* support for belgian structured communication format
* by default, the right part of the VAT number (KBO/BCE number) is used to identify the Initiating Party


Installation instructions
-------------------------

We recommend to run this module in combination with the following Noviat module:

- account_bank_statement_advanced


Assistance
----------

Contact info@noviat.com for help with the implementation of automated payment processing in Odoo.

