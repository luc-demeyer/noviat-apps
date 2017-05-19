.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Import Invoice Lines
====================

This module adds a button on the Supplier Invoice Form to allow the import of
invoice lines from a CSV file.

Usage
=====

**Input file column headers:**

- Description

- Product

  The value must be unique.
  A lookup will be peformed on the 'Internal Reference' (default_code) field of the Product record.
  In case of no result, a second lookup will be initiated on the Product Name.

- Unit of Measure

- Account

- Quantity

- Unit Price

- Taxes

  A lookup will be peformed on the 'Tax Code' (description) field of the Tax object.
  In case of no result, a second lookup will be initiated on the Tax Name.
  Use a comma as separator character to add multiple taxes.

- Analytic Account

Extra columns can be added and will be processed as long as
the column header is equal to the 'ORM' name of the field.
Input fields with no corresponding ORM field will be ignored.

A blank column header indicates the end of the columns that will be
processed. This allows 'comment' columns on the input lines.

Empty lines or lines starting with '#' will be ignored.

**Input file example:** 

Cf. directory 'sample_import_file' of this module.

Known Issues
============

This module uses the Python *csv* module for the reading of the input csv file.
The input csv file should take into account the limitations of the *csv* module:

Unicode input is not supported. Also, there are some issues regarding ASCII NUL characters.
Accordingly, all input should be UTF-8 or printable ASCII.
Results are unpredictable when this is not the case.
