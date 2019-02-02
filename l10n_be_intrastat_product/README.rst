.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=============================
Intrastat reports for Belgium
=============================


This module implements the Belgian Intrastat reporting.

The report can be reviewed and corrected where needed before
the creation of the XML file for the online declaration (ONEGATE).

More information can be found on the National Bank website:
https://www.nbb.be/en/statistics/foreign-trade


Installation
============

WARNING:

This module conflicts with the module *report_intrastat* and *l10n_be_intrastat*
from the official addons.
If you have already installed these modules,
you should uninstall them before installing this module.

Configuration wizard to load intrastat codes:
---------------------------------------------

The module comes with a configuration wizard that allows you to load the intrastat codes into the database.
The intrastat codes are available in 3 languages : english, dutch, french.

If your databases has been configured to support multiple languages, we recommend the following procedure so that
every user sees the intrastat code description in his own language:

1. Go to Settings -> Configuration Wizards and open the 'Load Intrastat Codes' wizard.
2. Change your Preferences to English
3. Load the intrastat codes, select the english csv file
4. Change your Preferences to Dutch
5. Load the intrastat codes, select the dutch csv file
6. Change your Preferences to French
7. Load the intrastat codes, select the french csv file

The system will load a large number of codes (9000+) hence this operation will take some time.

Configuration
=============

This module adds the following configuration parameters:

* Company

  - Arrivals : Exempt, Standard or Extended
  - Dispatches : Exempt, Standard or Extended
  - Default Intrastat Region
  - Default Intrastat Transaction
  - Default Intrastat Transport Mode (Extended Declaration)
  - Default Intrastat Incoterm (Extended Declaration)

* Warehouse

  - Intrastat Region to cope with warehouses in different regions

    The configuration of the Intrastat Region on a Warehouse, requires a login
    belonging to the "Belgian Intrastat Product Declaration" security group.

* Inrastat Codes, Supplementary Units, Transaction Tyoes, Transport Modes, Regions

  Cf. menu Accounting / Configuration / Miscellaneous / Intrastat Configuration

  The configuration data is loaded when installing the module.

  A configuration wizard also allows to update the Intrastat Codes so that you can easily
  synchronise your Odoo instance with the latest list of codes supplied with this module
  (an update is published on an annual basis by the Belgian National Bank).

  Some Intrastat Codes require an Intrastat Supplementary Unit.
  In this case, an extra configuration is needed to map the Intrastat Supplementary Unit
  to the corresponding Odoo Unit Of Measurement.

* Product

  You can define a default Intrastat Code on the Product or the Product Category.

Known issues / Roadmap
======================

- The current version of the Belgian Intrastat reporting module is only based on invoices.
  Since associated stock moves are not taken into consideration, it is possible that manual
  corrections are required, e.g.

  - Product movements without invoices are not included in the current version
    of this module and must be added manually to the report lines
    before generating the ONEGATE XML declaration.
  - Credit Notes are by default assumed to be corrections to the outgoing or incoming
    invoices within the same reporting period. The product declaration values of the
    Credit Notes are as a consequence deducted from the declaration lines.
    You should encode the Credit Note with 'Intrastat Transaction Type = 2' when the goods
    returned.

- The current version of the Belgian Intrastat reporting module does not perform a
  cross-check with the VAT declaration.

Assistance
----------

Contact info@noviat.com for help with the implementation of this module.
