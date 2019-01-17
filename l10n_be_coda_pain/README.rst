.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==============================================
CODA Import - ISO 20022 Payment Order Matching
==============================================

This Module adds logic to match CODA transactions with ISO 20022 Payment Order transactions.

Installation
============

There is nothing specific to do to install this module,

Known issues / Roadmap
======================

The current version of this module doesn't have matching logic for ISO 20022 Direct Debit Orders.

The matching logic for ISO 20022 Credit Transfers is currently limited to Payment Modes without
Transfer Accounts and non-grouped payments (hence direct reconcile with supplier invoice or customer credit note).
