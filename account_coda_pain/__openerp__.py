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
    'name': 'CODA Import - ISO 20022 Payment Order Matching',
    'version': '0.2',
    'author': 'Noviat',
    'category': 'Accounting & Finance',
    'complexity': 'normal',    
    'description': """
    This Module adds logic to match CODA transactions with ISO 20022 Payment Order transactions.
    """,
    'depends': ['account_coda', 'account_pain'],
    'demo_xml': [],
    'init_xml': [],
    'update_xml' : [
        'account_coda_view.xml',
    ],
    'active': False,
    'installable': True,
    'license': 'AGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
