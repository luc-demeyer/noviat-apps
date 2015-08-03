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
    'name': 'Bank Statement Usability improvements when using Analytic Plans',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'description': """
Bank Statement Uusability improvements
======================================

Install this module when using Analytic Plans (module account_analytic_plans)
in combination with the account_bank_statement_voucher module.

    """,
    'depends': [
        'account_bank_statement_voucher',
        'account_analytic_plans',
    ],
    'data': [
        'account_bank_statement_view.xml',
        'account_move_view.xml',
    ],
    'active': False,
    'installable': True,
    }
