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
    'name': 'Account Currency Enhancements',
    'version': '0.6',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category' : 'Accounting & Finance',
    "description": """
        This modules fixes a couple of issues when running accounting in a multi-currency environment
        including the support for general accounts with company currency as secondary currency (to enforce
        only entries in company currency on those accounts).
    """,
    'depends': ['account', 'account_voucher'],
    'demo_xml': [],
    "init_xml" : [],
    'update_xml' : [],
    }
