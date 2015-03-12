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
