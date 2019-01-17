.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================================================================
Multilanguage alternative for the 'l10n_be' belgian accounting module
=====================================================================

This module activates the following functionality:

    * Multilanguage support (en/nl/fr) for Chart of Accounts (CoA), Taxes
      and Tax Codes.
    * Multilingual accounting templates.
    * Support for the NBB/BNB legal Balance and P&L reportscheme including
      auto-configuration of the correct financial report entry when
      creating/changing a general account.
    * The account type will be automatically assigned
      based upon the account group when creating a new general account.
    * The setup wizard
        - allows to select mono- versus multilingual
          Chart of Accounts
        - allows to select which languages to install
        - copies the CoA, Tax, Tax Tags and Fiscal Position translations
          from the installation templates
    * Intervat XML VAT declarations
        - Periodical VAT Declaration
        - Periodical Intracom Declaration
        - Annual Listing of VAT-Subjected Customers

This module has been tested for use with Odoo Enterprise as well as Odoo Community.

Installation guidelines
=======================

It is recommended not to install l10n_be when using this module.

The l10n_be module is 'auto_installed' when creating a new database with the
Country field set to Belgium. As a consequence we recommend to leave this
field empty. The company country will be set to Belgium afterwards by the
l10n_be_coa_multilang setup wizard.

Configuration
=============

1) Chart of Accounts
--------------------

This module has a different approach than l10n_be for the population of the
Chart of Accounts (CoA).

The l10n_be module comes with a fully populated CoA whereas this module
will only create the CoA Groups and a strict minimum set of
general accounts.

In order to have a fully populated CoA, you have to import your own CoA
after the installation of this module.
You can use the standard account import button in order to do this.
When importing your chart of accounts the reporting tags and user type will
be set automatically based upon the account group (the first digits of the account code).

2) Fiscal Year
--------------

Configure your Fiscal Years via Accountint -> Configuration -> Date Ranges.

3) VAT Declarations
-------------------

By default the 'invoicing' contact of the Company is used as contact for the VAT Declarations.
Ensure that this contact has a valid e-mail and phone number since these fields
will be used for the Intervat XML VAT declarations.

Known issues / Roadmap
======================

 * Add extra controls to the VAT declaration wizards.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/luc-demeyer/noviat-apps/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.
