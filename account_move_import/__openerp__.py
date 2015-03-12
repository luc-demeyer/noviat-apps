# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category' : 'Accounting & Finance',
    'description': """

Import Accounting Entries
=========================

This module adds a button on the ‘Journal Entry’ screen to allow the import of the entry lines from a CSV file.

Before starting the import a number of sanity checks are performed:
- check if partner references are correct
- check if account codes are correct
- check if the sum of debits and credits are balanced

If no issues are found the entry lines will be loaded.\n
The resulting Journal Entry will be in draft mode to allow a final check before posting the entry.

The CSV file must have a header line with the following fields:

Mandatory Fields
----------------
- account (account codes are looked up via exact match)
- debit
- credit

Optional Fields
---------------
- name (if not specified, a '/' will be used as name
- partner (lookup logic : exact match on partner reference, if not found exact match on partner name)
- date_maturity (date format must be yyyy-mm-dd)
- amount_currency
- currency (specify currency code, e.g. 'USD', 'EUR', ... )
- tax_code (lookup logic : exact match on tax case 'code' field, if not found exact match on tax case 'name')
- tax_amount
- analytic_account

    """,
    'depends': ['account'],
    'data' : [
        'account_move_view.xml',
        'wizard/import_move_line_wizard.xml',
    ],
}
