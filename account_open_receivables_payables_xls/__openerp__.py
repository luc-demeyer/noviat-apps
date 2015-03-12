# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-now Noviat nv/sa (www.noviat.com).
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
    'name': 'Open Receivables/Payables XLS export',
    'version': '0.7',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Accounting & Finance',
    'description': """
Open Receivables/Payables XLS export
------------------------------------

This module adds the 'Open Receivables/Payables by Period' report to the
Accounting Partners reports.
The report is available in PDF and XLS format.
    """,
    'depends': ['account', 'report_xls'],
    'data': [
        'wizard/partner_open_arap.xml',
    ],
}
