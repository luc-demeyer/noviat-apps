# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2011 Noviat nv/sa (www.noviat.be). All rights reserved.
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
    'name': 'Cash Flow Management Operations',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Generic Modules/Accounting',
    'description': '''
Cash Management Operations: 
     1) Straigth Loan Demands
        Supported are Straight Loan Demands with following characteristics:
        - Option 1 : Single payment of principal and interest amount on the maturity date
        - Option 2 : Payment of interest at start date and principal amount on the maturity date
        - Day Count Basis : 360 or 365
        - Interest calculation formula : amount * rate * days/day_count_basis
        - Currency equal to currency of associated Bank Journal
        - Generation of Straight Load Demand letter meant for the Bank
        Confirming a Straight Loan Demand results in the following actions:
        - creation of a Cash Management Provision Entries
     2) Short Term Placements
        Functionality : idem as Straight Loand Demands

    ''',
    'depends': ['account_cashflow'],
    'demo_xml': [],
    'init_xml': [
        'data/account_cash_operation_data.xml',        
    ],
    'update_xml' : [
        'security/ir.model.access.csv',
        'account_cash_operation.xml',
        'account_cash_operation_report.xml',
    ],
    'active': False,
    'installable': True,
}
