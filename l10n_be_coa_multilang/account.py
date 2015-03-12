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

import re
from osv import fields, osv
from tools.translate import _
import netsvc
logger=netsvc.Logger()

class account_account_type(osv.osv):
    ''' add active flag to hide unused account types from UI '''
    _inherit = 'account.account.type'
    _columns = {
        'active': fields.boolean('Active', select=True),
    }
    _defaults = {
        'active': 1,
    }
account_account_type()

class account_account_template(osv.osv):
    _inherit = 'account.account.template'
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True, translate=True),
    }
account_account_template()

class account_account(osv.osv):
    _inherit = 'account.account'
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True, translate=True),
    }
account_account()

class account_tax_code(osv.osv):
    _inherit = 'account.tax.code'
    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the Tax Case must be unique per company !')
    ]
account_tax_code()

class account_tax_code_template(osv.osv):
    _inherit = 'account.tax.code.template'
    _columns = {
        'name': fields.char('Tax Case Name', size=64, required=True, translate=True),
    }
account_tax_code_template()

class account_chart_template(osv.osv):
    _inherit = 'account.chart.template'    
    _columns={
        'name': fields.char('Name', size=64, required=True, translate=True),
        'bank_from_template':fields.boolean('Banks/Cash from Template', help="Generate Bank/Cash accounts and journals from the Templates."),
    }
    _defaults = {
        'bank_from_template': False,
    }    
    _order = 'name'      
account_chart_template()

class account_fiscal_position_template(osv.osv):
    _inherit = 'account.fiscal.position.template'
    _columns = {
        'name': fields.char('Fiscal Position Template', size=64, required=True, translate=True),
        'note': fields.text('Notes', translate=True),        
    }
account_fiscal_position_template()

class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
        'name': fields.char('Journal Name', size=64, required=True, translate=True),
    }    
account_journal()        

class wizard_multi_charts_accounts(osv.osv_memory):
    """
    Change wizard that a new account chart for a company.
        * load nl & fr languages
        * Replace creation of financial accounts by copy from template.
          This change results in adherence to Belgian MAR numbering scheme for cash accounts.
        * Create financial journals for each account of type liquidity
    """
    _inherit = 'wizard.multi.charts.accounts'
    
    def onchange_chart_template_id(self, cr, uid, ids, chart_template_id=False, context=None):
        res = super(wizard_multi_charts_accounts, self).onchange_chart_template_id(cr, uid, ids, chart_template_id, context=context) 
        res_update = {}
        if chart_template_id:
            bank_from_template = self.pool.get('account.chart.template').browse(cr, uid, chart_template_id, context=context).bank_from_template
        res_update['bank_from_template'] = bank_from_template
        if bank_from_template:
            bank_accounts_id = []
        else:
            bank_accounts_id = self._get_default_accounts(cr, uid, context=context) 
        res_update['bank_accounts_id'] = bank_accounts_id
        res['value'].update(res_update)
        return res

    def copy_xlat(self, cr, uid, langs, in_obj, in_field, in_ids, out_obj, out_ids):
        # create ir.translation entries based upon 1-1 relationship between in_ and out_ params
        xlat_obj = self.pool.get('ir.translation')
        error = False
        if len(in_ids) != len(out_ids):
            logger.notifyChannel('addons.'+self._name, netsvc.LOG_ERROR,
                 'generate translations from template for %s failed (error 1)!' % out_obj._name)
            error = True
        else:
            cr.execute("SELECT id, " + in_field + " FROM " + in_obj._table + " WHERE id IN %s ORDER BY id", (tuple(in_ids),))
            sources = cr.fetchall()
            for lang in langs:
                cr.execute("SELECT res_id, src, value FROM ir_translation "  \
                           "WHERE name=%s AND type='model' AND lang=%s AND res_id IN %s "   \
                           "ORDER by res_id",
                           (in_obj._name + ',' + in_field, lang, tuple(in_ids)))
                xlats = cr.fetchall()
                if len(xlats) != len(filter(lambda x: x[1], sources)):
                    logger.notifyChannel('addons.'+self._name, netsvc.LOG_ERROR,
                        'generate translations from template for %s failed (error 2)!' % out_obj._name)
                    error = True
                else:
                    xi = 0
                    for i in range(len(out_ids)):
                        if sources[i][1]:
                            src = xlats[xi][1]
                            value = xlats[xi][2]
                            xi += 1
                            out_record = out_obj.browse(cr, uid, out_ids[i])
                            if getattr(out_record, in_field) != src:
                                logger.notifyChannel('addons.'+self._name, netsvc.LOG_ERROR,
                                     'generate translations from template for %s failed (error 3)!' % out_obj._name)
                                error = True
                            else:
                                xlat_obj.create(cr, uid, {
                                      'name': out_obj._name + ',' + in_field,
                                      'type': 'model',
                                      'res_id': out_record.id,
                                      'lang': lang,
                                      'src': src,
                                      'value': value,
                                })
        if error:
            raise osv.except_osv(_('Warning!'),
                 _('The generation of translations from the template for %s failed!'    \
                   '\nPlease report this issue via your OpenERP support channel.' % out_obj._name))

    def execute(self, cr, uid, ids, context=None):
        super(wizard_multi_charts_accounts, self).execute(cr, uid, ids, context=context)
        
        obj_multi = self.browse(cr, uid, ids[0], context=context)
        obj_mod = self.pool.get('ir.module.module')
        obj_acc_template = self.pool.get('account.account.template')
        obj_acc = self.pool.get('account.account')
        obj_tax_code_template = self.pool.get('account.tax.code.template')
        obj_tax_code = self.pool.get('account.tax.code')
        obj_tax_template = self.pool.get('account.tax.template')
        obj_tax = self.pool.get('account.tax')
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')
        obj_fiscal_position = self.pool.get('account.fiscal.position')
        obj_data = self.pool.get('ir.model.data')
        obj_sequence = self.pool.get('ir.sequence')
        analytic_journal_obj = self.pool.get('account.analytic.journal')
        obj_journal = self.pool.get('account.journal')

        company_id = obj_multi.company_id.id        
        acc_template_root_id = obj_multi.chart_template_id.account_root_id.id
        acc_root_id = obj_acc.search(cr, uid, [('company_id', '=', company_id), ('parent_id', '=', None)])[0]                       
        tax_code_template_root_id = obj_multi.chart_template_id.tax_code_root_id.id                    
        tax_code_root_id = obj_tax_code.search(cr, uid, [('company_id', '=', company_id), ('parent_id', '=', None)])[0]  
                        
        # load languates
        if obj_multi.load_dutch:
            if obj_multi.load_french:
                langs = ['nl_NL','fr_FR']
            else:
                langs = ['nl_NL']
            installed_mids = obj_mod.search(cr, uid, [('state', '=', 'installed')])
            for lang in langs:
                        obj_mod.update_translations(cr, uid, installed_mids, lang)

        # copy translations from templates
        langs = ['nl_NL','fr_FR']
        
        # copy account.account translations
        in_field = 'name'
        in_ids = obj_acc_template.search(cr, uid, [('id', 'child_of', [acc_template_root_id])], order='id')[1:]
        out_ids = obj_acc.search(cr, uid, [('id', 'child_of', [acc_root_id])], order='id')[1:]
        self.copy_xlat(cr, uid, langs, obj_acc_template, in_field, in_ids, obj_acc, out_ids)
        
        # copy account.tax.code translations
        in_field = 'name' 
        in_ids = obj_tax_code_template.search(cr, uid, [('id', 'child_of', [tax_code_template_root_id])], order='id')[1:]
        out_ids = obj_tax_code.search(cr, uid, [('id', 'child_of', [tax_code_root_id])], order='id')[1:]
        self.copy_xlat(cr, uid, langs, obj_tax_code_template, in_field, in_ids, obj_tax_code, out_ids)
        
        # copy account.tax translations
        in_field = 'name' 
        in_ids = sorted([x.id for x in obj_multi.chart_template_id.tax_template_ids])
        out_ids = obj_tax.search(cr, uid, [('company_id', '=', company_id)], order='id')
        self.copy_xlat(cr, uid, langs, obj_tax_template, in_field, in_ids, obj_tax, out_ids)
       
        # copy account.fiscal.position note field
        in_ids = obj_fiscal_position_template.search(cr, uid, [('chart_template_id', '=', obj_multi.chart_template_id.id)], order='id')
        out_ids = obj_fiscal_position.search(cr, uid, [('company_id', '=', company_id)], order='id')
        for i in range(len(in_ids)):
            fp_note = obj_fiscal_position_template.read(cr, uid, in_ids[i], ['note'])
            fp_note = fp_note['note']
            if fp_note:
                obj_fiscal_position.write(cr, uid, out_ids[i], {'note': fp_note})
        # copy account.fiscal.position translations
        in_fields = ['name', 'note']
        for in_field in in_fields:
            self.copy_xlat(cr, uid, langs, obj_fiscal_position_template, in_field, in_ids, obj_fiscal_position, out_ids)       
       
        # create bank journals
        if obj_multi.bank_from_template:
            vals_journal={}

            fin_code_ids = obj_acc_template.search(cr, uid, [('type', '=', 'liquidity'), ('id', 'child_of', [acc_template_root_id])], context=context)
            fin_codes = [x.code for x in obj_acc_template.browse(cr, uid, fin_code_ids, context=context)]
            fin_acc_ids = obj_acc.search(cr, uid, [('code', 'in', fin_codes)], context=context)
            fin_accs = obj_acc.browse(cr, uid, fin_acc_ids, context=context)

            data_id = obj_data.search(cr, uid, [('model','=','account.journal.view'), ('name','=','account_journal_bank_view')])
            data = obj_data.browse(cr, uid, data_id[0], context=context)
            view_id_cash = data.res_id
    
            data_id = obj_data.search(cr, uid, [('model','=','account.journal.view'), ('name','=','account_journal_bank_view_multi')])
            data = obj_data.browse(cr, uid, data_id[0], context=context)
            view_id_cur = data.res_id

            current_num = 1
            fin_ids = []
            for fin_acc in fin_accs:
                if fin_acc.code[0:2] == '55':
                    type = 'bank'
                elif fin_acc.code[0:2] == '57':
                    type = 'cash'
                else:
                    pass
                if obj_multi.seq_journal:
                    vals_seq={
                        'name': fin_acc.name,
                        'code': 'account.journal',
                    }
                    seq_id = obj_sequence.create(cr,uid,vals_seq)
    
                #create the bank journal
                analitical_bank_ids = analytic_journal_obj.search(cr,uid,[('type','=','situation')])
                analitical_journal_bank = analitical_bank_ids and analitical_bank_ids[0] or False
    
                vals_journal['name']= fin_acc.name
                vals_journal['code']= _('BNK') + str(current_num)
                vals_journal['sequence_id'] = seq_id
                vals_journal['type'] = type
                vals_journal['company_id'] =  company_id
                vals_journal['analytic_journal_id'] = analitical_journal_bank
    
                if fin_acc.currency_id:
                    vals_journal['view_id'] = view_id_cur
                    vals_journal['currency'] = line.currency_id.id
                else:
                    vals_journal['view_id'] = view_id_cash
                vals_journal['default_credit_account_id'] = fin_acc.id
                vals_journal['default_debit_account_id'] = fin_acc.id
                fin_id = obj_journal.create(cr, uid, vals_journal)
                fin_ids.append(fin_id)
                current_num += 1

            # copy bank journal translations
            in_field = 'name'
            self.copy_xlat(cr, uid, langs, obj_acc_template, in_field, fin_code_ids, obj_journal, fin_ids)       

    _columns = {
        'load_dutch': fields.boolean('Load Dutch Translation'),
        'load_french': fields.boolean('Load French Translation'),        
        'bank_from_template':fields.boolean('Banks/Cash from Template', 
            help="Generate Bank/Cash accounts and journals from the Templates." \
                 "Hide the 'bank_accounts_id' field on the 'view_wizard_multi_chart' view."),
    }
    _defaults = {
        'load_dutch' : True,
        'load_french' : True,        
        'bank_from_template': False,
    }
wizard_multi_charts_accounts()
