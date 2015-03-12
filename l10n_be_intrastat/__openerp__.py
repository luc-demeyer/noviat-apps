# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012-14 Agaplan (www.agaplan.eu) & Noviat (www.noviat.com).
#    All rights reserved.
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
    'name': 'Intrastat reports for Belgium',
    'version': '0.6',
    'description': """
This module contains the Belgian Intrastat reporting for Belgium.
More information can be found on the National Bank website:
http://www.nbb.be/pub/stats/foreign/foreign.htm?tab=Declarations.
    """,
    'category': 'Localisation/Report Intrastat',
    'author': 'Agaplan & Noviat',
    'depends': [
        "intrastat_base",
        "stock"
    ],
    'data': [
        'security/ir.model.access.csv',
        'company_view.xml',
        'intrastat_belgium_view.xml',
        'stock_view.xml',
    ],
    'installable': True,
}
