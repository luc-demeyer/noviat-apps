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
    'name': 'Belgium - CODA statements batch import',
    'version': '1.3',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Generic Modules/Accounting',
    'description': ''' 

Module to enable batch import of CODA bank statements.

The CODA files must be stored in an OpenERP Document Management Folder before the batch import.

A Log is created during the import in order to document import errors. 
If errors have been detected, the Batch Import Log state is set to 'error'.   
When all CODA Files have been imported correctly, the Batch Import Log state is set to 'done'.
    
The user can always redo the batch import until all errors have been cleared. 
    
As an alternative, the user can force the Batch Import Log state to 'done' (e.g. when the errors have been circumvented via single CODA file import or manual encoding).
       
    ''',
    'depends': ['account_coda','document_ftp'],
    'demo_xml': [],
    'init_xml': [],
    'update_xml' : [
        'security/ir.model.access.csv',
        'account_coda_batch_view.xml'
    ],
    'active': False,
    'installable': True,
}
