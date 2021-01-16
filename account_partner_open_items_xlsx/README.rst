.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==============================
Open Journal Items per partner
==============================

This module allows to export unreconciled Journals Items at a given date.

Usage
=====

Select a set of partners via the partners list view and call the report wizard via the 'Action' menu.
All general accounts which can be reconciled can be used as a filter.

This module is the successor of the 'account_open_payables_receivables_xls' module
published by Noviat for Odoo versions 6 to 8.

The look and feel of the Open Items details report has been aligned slightly with the 'Open Items' report
which comes with the OCA 'account_financial_report_qweb' module for Odoo 10.0.

The main differences with the OCA Open Items report are:

* This report is available via the action menu on the partner form and list views
  in order to facilitate the partner selection.

* The excel workbook contains multiple sheets in order to separate the transaction details and overview reports.

* The excel report is based upon a template which can be tailored easily (via res.partner inherit)


Assistance
----------

Contact info@noviat.com for help with the use of this module.
