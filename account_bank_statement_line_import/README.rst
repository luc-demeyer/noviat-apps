.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Import Bank Statement Lines
===========================

This module adds a button on the Bank Statement screen to allow the import of the statement lines from a CSV file.

Before starting the import a number of sanity checks are performed such as:

- check if partner references are correct

If no issues are found the lines will be loaded.


Usage
=====

Input file column headers
-------------------------

Mandatory Fields
''''''''''''''''

- Entry Date (or date)

- Amount

Other Fields
''''''''''''

Extra columns can be added and will be processed as long as
the column header is equal to the 'ORM' name of the field.
Input fields with no corresponding ORM field will be ignored
unless special support has been added for that field in this
module (or a module that extends the capabilities of this module).

This module has implemented specific support for the following fields:

- Communication (or name)

  If not specified, a '/' will be used as name.

- Partner

  The value must be unique.
  Lookup logic : exact match on partner reference,
  if not found exact match on partner name.

  
- Value Date (or val_date)

  Date format must be yyyy-mm-dd)


A blank column header indicates the end of the columns that will be
processed. This allows 'comment' columns on the input lines.

Empty lines or lines starting with '#' will be ignored.

Input file example
------------------

Cf. directory 'sample_import_file' of this module.

Known Issues
============

This module uses the Python *csv* module for the reading of the input csv file.
The input csv file should take into account the limitations of the *csv* module:

Unicode input is not supported. Also, there are some issues regarding ASCII NUL characters.
Accordingly, all input should be UTF-8 or printable ASCII.
Results are unpredictable when this is not the case.

Credits
=======

Author
------

* Luc De Meyer, Noviat <info@noviat.com>

