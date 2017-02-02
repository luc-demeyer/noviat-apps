.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Sale Discount Advanced
======================

This module allows to define discount policies based upon order or order line values.

This concept is different from the standard Odoo pricelist concept which allows to define price discount based
upon ordered quantities on a per sale order line (hence without consideration of total order value).

Installation
============

There is no specific installation procedure for this module.

Configuration
=============

To configure this module, you need to:

* Go to Sales > Configuration > Discounts

  to create your discount policies.

* Go to Sales > Configuration > Pricelists

  to add the Sale Discounts to your Sale Pricelist.

* Go to Settings > Users

  We recommend to set the 'Discount on lines' option.

Usage
=====

Once the disoounts are configured, the discount policies will be applied automatically
to the order lines based upon the selected pricelist.

You can also manually add extra discount policies on the order lines.

Known issues
============

There no known issues at this point in time.

Roadmap
=======

Addition or demo data and unit tests.

Credits
=======

Contributors
------------
- ICTSTUDIO, André Schenkels"
- Noviat, Luc De Meyer
* Dennis Sluijk <d.sluijk@onestein.nl>
