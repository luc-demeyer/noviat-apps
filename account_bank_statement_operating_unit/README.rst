.. image:: https://img.shields.io/badge/license-AGPLv3-blue.svg
   :target: https://www.gnu.org/licenses/agpl.html
   :alt: License: AGPL-3

===========================================
Encode Bank Statements with Operating Units
===========================================

Adds the Operating Unit (OU) to the Bank Statement.

The Bank Statement OU is defaulted to the OU of the user.

Accounting entries generated from the Bank Transactions will be handled as follows:

- The entry representing the money in/out will be set to the OU of the Bank Statement.
- The counterparty entry/entries will be defaulted to the OU of the Bank Statement.
  This default can be changed manually via the "reconcile" widget,
  e.g. to assign banks costs to multiple Organisation Units.
