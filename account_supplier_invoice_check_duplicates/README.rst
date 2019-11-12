.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

====================================
Supplier Invoices - Check duplicates
====================================

This module adds logic to prevent entering two times the same supplier invoice.

By default a duplicate is detected when there is already an open or paid invoice
with 

- same supplier
- same supplier invoice number

In case no supplier invoice number has been encoded extra checks are added to detect duplicates :

- same date
- same amount

This logic can be customized via the _get_dup_domain method.

The duplicate checking can be bypassed via the 'Force Encoding' flag.

Known issues / Roadmap
======================

- Align this module with the OCA 'account_invoice_supplier_ref_unique' module.
