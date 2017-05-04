.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================
Account Reinvoice Multi-Company
===============================

Install this module to facilitate intercompany reinvoicing
when you have several legal entities (Companies) in the same Odoo database.

Customer Invoices/Refunds to Companies in the same database will be
automatically converted into Supplier Invoices/Refunds in the target company
when validating the outgoing Invoices/Refunds.

Configuration
=============

Company settings
----------------

Ensure to share the 'Partner' record associated to a Company between the Companies in the Odoo database.

You can do this without changing the default Company Record Rules by setting the 'Company' field of the associated
Partner to blank.

Set the 'Intercompany Invoice' flag on the Company's partner record (cf. Intercompany notebook page).

Define also the 'Intercompany Invoice User' which should be a user
with Invoice create access rights in the target Company.

It is recommended to create a dedicated User for this purpose.

You can disable the 'active' flag since this is a 'technical' user which will not be used
by a real End User.

As a consequence these users will not impact the 'Active User Count' which forms the basis
for the Odoo Enterprise subscription pricing.


Product Records
---------------

Products must be specified on all lines of the outgoing intercompany invoices.
These products must be shared between the Companies.

The product record accounting properties will be used for the incoming invoice line general account and taxes.

Journal Mapping
---------------

Go to **Accounting > Configuration > Miscellaneous > Reinvoice Configuration > Journal Mapping multi-company**

Use this menu entry to configure the mapping between the Outgoing Sales/Sales Refund Journals and the
incoming Purchase/Purchase Refund Journals in the target company.
