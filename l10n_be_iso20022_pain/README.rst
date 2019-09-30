.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
ISO 20022 PAIN Support for Belgium
==================================

This module adds Belgium-specific support to OCA/bank-payment/account_payment_order.

* support of the BBA structured communication type [1]

Reference information can be found in
* https://www.febelfin.be/fr/paiements/directives-et-protocoles-standards-bancaires
* https://www.febelfin.be/nl/betaalverkeer/richtlijnen-en-protocollen-bankstandaarden
* [1] https://www.febelfin.be/sites/default/files/Payments/AOS-OGMVCS.pdf

Installation
============

There is nothing specific to do to install this module,
except having the dependent modules available in your addon path.

It is recommended to install l10n_be_invoice_bba, and you will
probably want to use account_banking_sepa_credit_transfer and/or
account_banking_sepa_direct_debit.

Usage
=====

This module adds a new 'Belgium BBA' communication types on payment lines.
When adding invoices to payment orders, invoices having this BBA communication type
automatically put the correct communication type on payment lines. Generated
PAIN files then use the correct communication type.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Thomas Binsfeld <thomas.binsfeld@acsone.eu>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.

