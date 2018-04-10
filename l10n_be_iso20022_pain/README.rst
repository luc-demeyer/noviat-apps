.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

================================================================
ISO 20022 Supplier payment with Belgian structured communication
================================================================

This modules adds Belgium-specific support to OCA/bank-payment
payment initiation modules (account_banking_pain_base).

* support of the BBA structured communication type [1]

Reference information can be found in
* https://www.febelfin.be/fr/paiements/directives-et-protocoles-standards-bancaires
* https://www.febelfin.be/nl/betaalverkeer/richtlijnen-en-protocollen-bankstandaarden
* [1] https://www.febelfin.be/sites/default/files/Payments/AOS-OGMVCS.pdf

Installation
============

There is nothing specific to do to install this module,
except having the dependent modules available in your addon path.

It is recommended to install l10n_be_invoice_bba_supplier, and you will
probably want to use account_banking_sepa_credit_transfer and/or
account_banking_sepa_direct_debit.

Configuration
=============

None.

Usage
=====

This module adds a new 'Belgium BBA' communication types on payment lines.
When adding invoices to payment orders, invoices having this BBA communication type
automatically put the correct communication type on payment lines. Generated
PAIN files then use the correct communication type.

Known issues / Roadmap
======================

None.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-belgium/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-belgium/issues/new?body=module:%20l10n_be_iso20022_pain%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Luc De Meyer <luc.demeyer@noviat.be>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
