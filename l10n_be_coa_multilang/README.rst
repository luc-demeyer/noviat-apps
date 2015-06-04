.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Multilanguage alternative for the 'l10n_be' belgian accounting module.
======================================================================

This module activates the following functionality:

    * Multilanguage support (en/nl/fr) for Chart of Accounts (CoA), Taxes
      and Tax Codes.
    * Multilingual accounting templates.
    * Support for the NBB/BNB legal Balance and P&L reportscheme including
      auto-configuration of the correct financial report entry when
      creating/changing a general account
    * The setup wizard
        - allows to select mono- versus multilingual
          Chart of Accounts
        - allows to select which languages to install
        - copies the CoA, Tax, Tax Code and Fiscal Position translations
          from the installation templates
    * Intervat XML VAT declarations
        - Periodical VAT Declaration
        - Periodical Intracom Declaration
        - Annual Listing of VAT-Subjected Customers
    * Standard accounting module enhancements
        - Allow 'Deferral Method' = 'Balance'
          on Accounts Payable and Receivable (AP/AR) accounts
        - Add constraint to ensure unique Tax Code per Company
        - Replace Tax Object (account.tax) unique on (name, company_id)
          constraint by unique on (name, description, company_id)
        - Improved multi-company support via 'active' and 'company_id'
          fields on 'account.account.type'

Installation guidelines
=======================

In order to have the XBRL codes in the NBB/BNB legal reports, a patch must be installed on your Odoo instance (cf. https://github.com/odoo/odoo/pull/6923).
Install the diff file distributed with this module (cf. doc/account_financial_report.diff).

Configuration
=============

This module has a different approach than l10n_be for the population of the
Chart of Accounts (CoA).

The l10n_be module comes with a fully populated CoA whereas this module
will only create the CoA Classes, Groups and a strict minimum set of
general accounts.

In order to have a fully populated CoA, you have to import the customer's
CoA after the installation of this module.

As an alternative, you can first install the l10n_be module to get a
fully populated CoA and afterwards uninstall l10n_be and install this module.

Known issues / Roadmap
======================

 * Add extra controls to the VAT declaration wizards.

Credits
=======

Author
------
* Noviat <info@noviat.com>

Contributors
------------
* acsone <info@acsone.eu>

Maintainer
----------
.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.