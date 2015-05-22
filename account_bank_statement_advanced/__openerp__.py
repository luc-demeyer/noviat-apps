# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
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
    'name': 'Advanced Bank Statement',
    'version': '0.7',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Accounting & Finance',
    'summary': 'Advanced Bank Statement',
    'depends': [
        'account',
        'account_cancel',
        'base_iban',
        'web_sheet_full_width_selective',
    ],
    'conflicts': ['account_bank_statement_extensions'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'data/data.xml',
        'account_bank_statement_view.xml',
        'account_move_view.xml',
        'wizard/bank_statement_balance_print.xml',
        'report/reports.xml',
        'views/report_layout.xml',
        'views/report_statement_balances.xml',
    ],
}
