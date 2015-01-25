Import Accounting Entries
=========================

This module adds a button on the ‘Journal Entry’ screen to allow the import of the entry lines from a CSV file.

Before starting the import a number of sanity checks are performed:

- check if partner references are correct
- check if account codes are correct
- check if the sum of debits and credits are balanced

If no issues are found the entry lines will be loaded.
The resulting Journal Entry will be in draft mode to allow a final check before posting the entry.

The CSV file must have a header line with the following fields:

Mandatory Fields
----------------
- account (account codes are looked up via exact match)
- debit
- credit

Optional Fields
---------------
- name (if not specified, a '/' will be used as name
- partner (lookup logic : exact match on partner reference, if not found exact match on partner name)
- date_maturity (date format must be yyyy-mm-dd)
- amount_currency
- currency (specify currency code, e.g. 'USD', 'EUR', ... )
- tax_code (lookup logic : exact match on tax case 'code' field, if not found exact match on tax case 'name')
- tax_amount
- analytic_account
