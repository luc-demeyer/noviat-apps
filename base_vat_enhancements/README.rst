base_vat module performance enhancements
========================================

This module contains the following performance improvements:

- VIES VAT on-line check performance improvements

  The standard base_vat module behaviour is changed as follows:

  When the VIES VAT option has been set on the Company an on-line check will be performed
  via the TIN Number "Check Validity" button.

  When performing partner record updates (explicitly or implicitly e.g. by paying an invoice), a VAT number check is performed
  on partner and/or contact records (since the VAT number is part of the so-called "_commercial_fields").
  Since the on-line check may slow down considerably the regular operations, the constraint has been removed and replaced by
  an on-line check when creating partner records and a basic off-line check when updating partner records.

- normalize res.partner vat field in the database to improve search performance

- normalize search argument when searching on VAT number
