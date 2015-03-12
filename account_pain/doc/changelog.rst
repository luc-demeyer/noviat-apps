.. _changelog:

Changelog
=========

`Version 7.0.0.2`
----------------

- Non-SEPA payments are now supported.

`Version 7.0.0.3`
----------------

- ``supplier_direct_debit`` field (boolean)
  This is a new field on the ``res.partner`` and ``account.invoice`` objects.
  Supplier Invoices with this flag will not be included in the Payment Order 'Select Invoices to Pay' selection.

