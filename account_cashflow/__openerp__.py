# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.be). All rights reserved.
# 
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Cash Flow Management',
    'version': '1.5',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Generic Modules/Accounting',
    'description': '''
Cash Management via Bank Statement Processing.

Functionality offered by this module:
- Rules Engine to assign Cash Flow Codes to Bank Statement Lines
- Wizard to assign Cash Flow Codes to groups of bank transaction
- Provisions for cash forecasting purposes
- Reporting

    ''',
    'depends': ['account_bank_statement_extensions', 'report_webkit'],
    'demo_xml': [],
    'init_xml': [
        'data/account_cashflow_data.xml',
    ],
    'update_xml' : [
        'security/ir.model.access.csv',
        'account_cashflow_view.xml',
        'report/account_cashflow_report_layout.xml',
        'account_cashflow_report.xml',
        'wizard/account_cashflow_chart_wizard.xml',
        'wizard/assign_cashflow_code_wizard.xml',
        'wizard/reconcile_cashflow_line_wizard.xml',
        'wizard/confirm_cashflow_line_wizard.xml',
        'wizard/cancel_cashflow_line_wizard.xml',
        'wizard/calc_cashflow_balance_wizard.xml',      
        'wizard/calc_cashflow_opening_balance_wizard.xml',    
        'wizard/cancel_cashflow_opening_balance_wizard.xml',                
    ],
    'active': False,
    'installable': True,
}
