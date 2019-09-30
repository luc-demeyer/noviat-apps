.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=======================
Advanced Bank Statement
=======================

This module extends the standard account_bank_statement object for
better scalability and e-banking support.

This module adds:
-----------------
- value date
- batch payments
- Payment Reference field to support ISO 20022 EndToEndReference
  (simple or batch. detail) or PaymentInformationIdentification (batch)
- Creditor Reference fields to support ISO 20022 CdtrRefInf
  (e.g. structured communication & communication type)
- bank statement line views
- bank statements balances report
- performance improvements for digital import of bank statement
- manual reconcile extended to partners which are not marked as 'customer' or 'supplier'
