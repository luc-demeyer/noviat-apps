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
    'name': 'Outgoing Invoices interface to Cash Flow Management',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Generic Modules/Accounting',
    'description': """ 
Outgoing Invoices interface to Cash Flow Management: 
Creation of Cash Management Provision Lines for outgoing Invoices and incoming Refunds.
Install the 'account_cashflow_payment' module for incoming Invoices and outgoing Refunds. 

    """,
    'depends': ['account_cashflow'],
    'demo_xml': [],
    'init_xml': [],
    'update_xml': [
        'account_invoice_view.xml',
        'account_invoice_workflow.xml',
    ],
    'active': False,
    'installable': True,
}
