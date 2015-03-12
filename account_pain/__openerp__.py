# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2012 Noviat nv/sa (www.noviat.be). All rights reserved.
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
    'name': 'Generate ISO 20022 XML payment files',
    'version': '1.6',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Generic Modules/Accounting',
    'description': """ 
    Module to generate Customer Credit Transfer Initiation message ISO 20022 XML - pain.001.001.03.

    This module implements the following subset of the febelfin guidelines:
        European Credit Transfers: 
        - debtor and creditor account in SEPA countries
        - debtor account in Euro
        - creditor account in Euro
        - creditor account identified by IBAN for BE IBAN accounts
        - creditor account identified by BIC & IBAN for non-BE IBAN accounts
        - support for single payments
        - support for belgian structured communication format
        
    The module also prohibits the removal of a confirm Payment Order. 
    Such a removal is still possible via the 'Undo Payment' button available to users of the 'Accounting / Manager' group.
    """,
    'depends': ['account','base_iban', 'account_payment'],
    'demo_xml': [],
    'init_xml': [],
    'update_xml' : [
#        'security/ir.model.access.csv',
        'account_pain_wizard.xml',
        'payment_view.xml',      
    ],
    'active': False,
    'installable': True,
}
