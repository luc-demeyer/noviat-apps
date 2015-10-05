# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    'name': 'Accounting Entries Import when using Analytic Plans',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'description': """
Install this module when using Analytic Plans (module account_analytic_plans)
in combination with the account_move_import module.

This module adds support for the following field in the input csv:

- Analytic Distribution (or analytic_distribution)

  Lookup logic : exact match on code,
  if not found exact match on name.

    """,
    'depends': [
        'account_move_import',
        'account_analytic_plans',
    ],
    'installable': True,
    'auto_install': True,
    }
