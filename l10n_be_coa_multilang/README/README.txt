Installation tips
=================

1) Replace the l10n_be module from OpenERP with the version included with this module.
2) Apply the account_financial_report.diff patch.
3) Reporting entries will not be created when you are installing this module for a Company for which the CoA has already been created (e.g PCMN from l10n_be). 
   In such a case, you should make a script to rewrite the accounts.
   

Changes in V2.4
===============

Periodical VAT declaration print button. 
   
Changes in V2.5
===============

The following reports are no longer bundled with this module: 

- Open Payables/Receivables by Period
- Open Payables/Receivables by Fiscal Year

The first report is now available via the 'account_open_receivables_payables_xls' module.
The second report is no longer available since you get the same result when selecting the FY Close period in the first report.

   
Changes in V2.6
===============

The following reports are no longer bundled with this module: 

- Print Journal by Period
- Print Journal by Fiscal Year

These reports are now available via the 'account_journal_report_xls' module.
   