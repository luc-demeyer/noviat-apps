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

from osv import fields,osv
from tools.translate import _
from lxml import etree
import time
import base64
import netsvc
logger=netsvc.Logger()

class account_coda_batch_import(osv.osv_memory):
    _name = 'account.coda.batch.import'
    _description = 'CODA Batch Import'
       
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_coda_batch_import, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        # add domain filter to directory_id
        view_obj = etree.XML(res['arch'])
        find = etree.XPath("/form/group/field[@name='directory_id']")
        directory_id = find(view_obj)
        batch_config_obj = self.pool.get('account.coda.batch.config')        
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        dir_id = batch_config_obj.search(cr, uid, [('company_id', '=', company_id)], context=context)[0]
        parent_dir = batch_config_obj.browse(cr, uid, dir_id, context=context).directory_id
        folders = parent_dir.child_ids           
        folder_ids = [x.id for x in folders]
        if not folder_ids: 
            raise osv.except_osv('Warning', _('No CODA Folders found within %s!') % parent_dir.name)
        domain = [('id', 'in', folder_ids)]
        for el in directory_id:
            el.set('domain', str(domain))
            res['arch'] = etree.tostring(view_obj)
        #logger.notifyChannel('addons.'+self._name, netsvc.LOG_WARNING, 'arch = %s' % etree.tostring(view_obj))
        return res
    
    _columns = {
        'directory_id': fields.many2one('document.directory', 'CODA Batch Import Folder', required=True,
            help='Folder containing the CODA Files for the batch import.'),
        'note':fields.text('Batch Import Log', readonly=True),
    }
        
    def coda_batch_import(self, cr, uid, ids, context=None, restart=False):
        if context is None:
            context = {}

        dir_obj = self.pool.get('document.directory')
        log_obj = self.pool.get('account.coda.batch.log')
        mod_obj = self.pool.get('ir.model.data')
        import_wiz = self.pool.get('account.coda.import')

        if restart:
            if context.get('active_model', False) == 'account.coda.batch.log':
                log_id = context.get('active_id', False)
                log = log_obj.browse(cr, uid, log_id)
                directory_id = log.directory_id.id
                directory_name = log.directory_id.name
                note = log.note or ''
        else:
            data=self.browse(cr, uid, ids)[0]
            try:
                directory_id = data.directory_id.id
                directory_name = data.directory_id.name
                note = ''
            except:
                raise osv.except_osv(_('Error!'), _('Wizard in incorrect state. Please hit the Cancel button!'))
                return {}
            
        folder = dir_obj.browse(cr, uid, directory_id, context=context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context).name
        log_header = _('>>> %s Import by %s. Results:') % (time.strftime('%Y-%m-%d %H:%M:%S'), user)
        log_footer = _('\n\nNumber of files : %s\n\n') % str(len(folder.file_ids))
        log_note = ''
        nb_err = 0
        err_log = ''

        if not restart:
            log_id = log_obj.create(cr, uid,{
                'name' : directory_name,
                'directory_id' : directory_id,
                'state': 'draft',
                })
        context.update({'log_id': log_id})
        cr.commit()

        # sort CODA files on creation date
        coda_files = []
        for file_id in folder.file_ids:
            coda_creation_date = False
            codafile=str(file_id.datas)
            codafilename=file_id.datas_fname
            recordlist = unicode(base64.decodestring(codafile), 'windows-1252', 'strict').split('\n')
            if not recordlist:
                    nb_err += 1
                    err_log += _("\n\nError while processing CODA File '%s' :") % (codafilename)
                    err_log += _("\nEmpty File !")
            else :
                for line in recordlist:
                    if not line:
                        pass
                    elif line[0] == '0':
                        try:
                            coda_creation_date = str2date(line[5:11])
                            if line[16] == 'D':
                                nb_err += 1
                                err_log += _("\n\nError while processing CODA File '%s' :") % (codafilename)
                                err_log += _("\nThis CODA File is marked by your bank as a 'Duplicate' !")                                
                                err_log += _('\nPlease treat this CODA File manually !')                                
                            else:
                                coda_files += [(coda_creation_date, file_id)]
                        except:
                            nb_err += 1
                            err_log += _("\n\nError while processing CODA File '%s' :") % (codafilename)
                            err_log += _('\nInvalid Header Record !')
                        break
                    else:
                        nb_err += 1
                        err_log += _("\n\nError while processing CODA File '%s' :") % (codafilename)
                        err_log += _("\nMissing Header Record !")
                        break
        coda_files.sort()

        # process CODA files
        for coda_file in coda_files:
            file_id = coda_file[1]
            time_start = time.time()
            res = import_wiz.coda_parsing(cr, uid, ids, context=context, 
                batch=True, codafile=file_id.datas, codafilename=file_id.datas_fname)
            file_import_time = time.time() - time_start
            logger.notifyChannel('addons.'+self._name, netsvc.LOG_INFO, 'File %s processing time = %.3f seconds' % (file_id.datas_fname, file_import_time))
            if res:
                if res[0][0] == 'W':
                    err_log += _("\n\nWarning while processing CODA File '%s' :") % file_id.datas_fname + res[1]
                else:
                    nb_err +=1
                    err_log += _("\n\nError while processing CODA File '%s' :") % file_id.datas_fname + res[1]                    
            else:
                log_note += _("\n\nCODA File '%s' has been imported.") % file_id.datas_fname

        if nb_err:
            log_note = log_note + _('\n\nNumber of errors : ') + str(nb_err)
            log_state = 'error'
        else:
            log_state = 'done'

        note = note + log_header + err_log + log_note + log_footer

        log_obj.write(cr, uid,[log_id], {
            'note': note,
            'state': log_state,
            })

        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'account_coda_batch_import_result_view')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        if restart:
            return True
        else:
            self.write(cr, uid, ids, {'note': note}, context=context)
            return {
                'name': _('CODA Batch Import result'),
                'res_id': ids[0],
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.coda.batch.import',
                'view_id': False,
                'target': 'new',
                'views': [(resource_id, 'form')],
                'context': context,
                'type': 'ir.actions.act_window',
            }

    def action_open_log(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return {
            'domain': "[('id','=',%d)]" %(context.get('log_id', False)),
            'name': _('CODA Batch Import Log'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.coda.batch.log',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

account_coda_batch_import()

def str2date(date_str):
    return time.strftime('%Y-%m-%d', time.strptime(date_str,'%d%m%y'))