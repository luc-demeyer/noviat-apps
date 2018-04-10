.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================================
Supplier Invoices - Check duplicates
====================================

This module adds logic to prevent entering two times the same supplier invoice.

By default a duplicate is detected when there is already an open or paid invoice
with 

- same supplier
- same supplier invoice number
- same date
- same amount

This logic can be cujstomized via the _get_dup_domain method.

The duplicate checking can be bypassed via the 'Force Encoding' flag.
