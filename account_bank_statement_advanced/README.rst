.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

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
- search on res.partner.bank enhanced to ignore spaces and '-' characters
- return IBAN if search initiated with BBAN (currently only for Belgium)

Installation guidelines
=======================

This module requires that your Odoo instance runs a version that includes the
following Pull Requests:

- https://github.com/odoo/odoo/pull/8396
- https://github.com/odoo/odoo/pull/8397

You should install the patch distributed with this module if this is not the case:
doc/account_bank_statement.diff
