# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Account Move Import',
    'version': '0.2',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Import Accounting Entries',
    'depends': ['account'],
    'description': """
Import Accounting Entries
=========================

This module adds a button on the ‘Journal Entry’ screen to allow
the import of the entry lines from a CSV file.

Before starting the import a number of sanity checks are performed such as:

- check if partner references are correct
- check if account codes are correct
- check if the sum of debits and credits are balanced

If no issues are found the entry lines will be loaded.
The resulting Journal Entry will be in draft mode to allow
a final check before posting the entry.

The CSV file must have a header line with the following fields:

Usage
=====

Input file column headers
-------------------------

Mandatory Fields
''''''''''''''''

- Account

  Account codes are looked up via exact match.

- Debit

- Credit

Other Fields
''''''''''''

Extra columns can be added and will be processed as long as
the column header is equal to the 'ORM' name of the field.
Input fields with no corresponding ORM field will be ignored
unless special support has been added for that field in this
module (or a module that extends the capabilities of this module).

This module has implemented specific support for the following fields:

- Name

  If not specified, a '/' will be used as name.

- Partner

  The value must be unique.
  Lookup logic : exact match on partner reference,
  if not found exact match on partner name.

- Product

  The value must be unique.
  A lookup will be peformed on the 'Internal Reference' (default_code) field
  of the Product record.
  In case of no result, a second lookup will be initiated on the Product Name.

- Due date (or date_maturity)

  Date format must be yyyy-mm-dd)

- Currency

  Specify currency code, e.g. 'USD', 'EUR', ... )

- Tax Account (or tax_code)

  Lookup logic : exact match on tax case 'code' field,
  if not found exact match on tax case 'name'.

- Analytic Account (or analytic_account)

  Lookup logic : exact match on code,
  if not found exact match on name.

A blank column header indicates the end of the columns that will be
processed. This allows 'comment' columns on the input lines.

Empty lines or lines starting with '#' will be ignored.

Input file example
------------------

Cf. directory 'sample_import_file' of this module.

Known Issues
============

This module uses the Python *csv* module
for the reading of the input csv file.
The input csv file should take into account the limitations
of the *csv* module:

Unicode input is not supported.
Also, there are some issues regarding ASCII NUL characters.
Accordingly, all input should be UTF-8 or printable ASCII.
Results are unpredictable when this is not the case.
    """,
    'data': [
        'views/account_move.xml',
        'wizard/import_move_line_wizard.xml',
    ],
    'demo': [
        'demo/account_move.xml',
    ],
    'installable': True,
}
