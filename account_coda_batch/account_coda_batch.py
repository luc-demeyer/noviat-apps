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

import time
from osv import osv, fields
import netsvc
from tools.translate import _
logger=netsvc.Logger()

class account_coda_batch_config(osv.osv):
    _name= 'account.coda.batch.config'
    _description= 'CODA Batch Import Configuration'
    _rec_name = 'directory_id'

    _columns = {
        'directory_id': fields.many2one('document.directory', 'Root Directory', required=True, 
            help='Root Directory for the CODA Batch Import folders.'),
        'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the Bank Account without removing it.'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'active': True,                 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
account_coda_batch_config()

class account_coda_batch_log(osv.osv):
    _name = 'account.coda.batch.log'
    _description = 'Object to store CODA Batch Import Logs'
    _order = 'name desc'
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'directory_id': fields.many2one('document.directory', 'CODA Batch Import Folder', required=True,
            readonly = True, help='Folder containing the CODA Files for the batch import.'),
        'note': fields.text('Batch Import Log', readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('error', 'Error'),            
            ('done', 'Done')], 
            'State', required=True, readonly=True),
        'date': fields.date('Log Creation Date', readonly=True),
        'user_id': fields.many2one('res.users','User', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True)
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'user_id': lambda self,cr,uid,context: uid,
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.coda', context=c),
    }        
    _sql_constraints = [
        ('dir_uniq', 'unique (directory_id)', 'This folder has already been processed !')
    ]  

    def button_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    def button_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True
    
    def button_import(self, cr, uid, ids, context=None):
        batch_import_wiz = self.pool.get('account.coda.batch.import')
        context.update({
            'active_model': 'account.coda.batch.log',
            'active_ids': ids,
            'active_id': ids[0]
        })
        res = batch_import_wiz.coda_batch_import(cr, uid, ids, context=context, restart=True)
        return True

    def unlink(self, cr, uid, ids, context=None):
        state = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in state:
            if s['state'] in ('draft'):
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _("Only log objects in state 'draft' can be deleted !"))
        return super(account_coda_batch_log, self).unlink(cr, uid, unlink_ids, context=context)

account_coda_batch_log()
