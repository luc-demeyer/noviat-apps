# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com).
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
    'name': 'Fix onchange on binary fields',
    'version': '0.1',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Web',
    'complexity': 'normal',
    'description': """
Web module to fix onchange on binary fields
===========================================

This module fixes the following problem:

Return correct filename for onchange on a binary field.

    """,
    'depends': ['web'],
    'data': [
        'view/fix_binaryfile_widget.xml',
    ],
    'auto_install': False,
}
