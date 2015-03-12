# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class wizard_multi_charts_accounts(orm.TransientModel):
    """
    Change wizard that creates a new account chart for a company.
        * update company_id country to Belgium
        * load nl & fr languages
        * Replace creation of financial accounts by copy from template.
          This change results in adherence to Belgian MAR numbering scheme for cash accounts.
        * Create financial journals for each account of type liquidity
    """
    _inherit = 'wizard.multi.charts.accounts'
    
    def onchange_chart_template_id(self, cr, uid, ids, chart_template_id=False, context=None):
        res = super(wizard_multi_charts_accounts, self).onchange_chart_template_id(cr, uid, ids, chart_template_id, context=context) 
        obj_chart_template = self.pool.get('account.chart.template')
        res_update = {}
        if chart_template_id:
            chart_template = obj_chart_template.browse(cr, uid, chart_template_id, context=context)
            multilang_be = chart_template.multilang_be
            res_update['multilang_be'] = multilang_be
        res['value'].update(res_update)
        return res

    def copy_xlat(self, cr, uid, langs, in_obj, in_field, in_ids, out_obj, out_ids):
        # create ir.translation entries based upon 1-1 relationship between in_ and out_ params
        xlat_obj = self.pool.get('ir.translation')
        error = False
        if len(in_ids) != len(out_ids):
            _logger.error('generate translations from template for %s failed (error 1)!', out_obj._name)
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
                    _logger.warn('generate translations from template for %s failed (template translations incomplete, lang = %s)!', out_obj._name, lang)
                else:
                    xi = 0
                    for i in range(len(out_ids)):
                        if sources[i][1]:
                            src = xlats[xi][1]
                            value = xlats[xi][2]
                            xi += 1
                            out_record = out_obj.browse(cr, uid, out_ids[i], context={'lang':'en_US'})
                            if getattr(out_record, in_field) != src:
                                _logger.error("generate translations from template %s (id:%s) failed (error 3)!" \
                                    "\n%s,%s = '%s' i.s.o. '%s'.",
                                    in_obj._name, xlats[xi][0], out_record, in_field, getattr(out_record, in_field), src)
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
            raise orm.except_orm(_('Warning!'),
                 _('The generation of translations from the template for %s failed!'    \
                   '\nPlease report this issue via your OpenERP support channel.' % out_obj._name))

    def execute(self, cr, uid, ids, context=None):
        # update company country (required for auto-configuration of the legal financial reportscheme)
        obj_multi = self.browse(cr, uid, ids[0], context=context)
        company_id = obj_multi.company_id.id  
        be_country_id = self.pool.get('res.country').search(cr, uid, [('code', '=', 'BE')])[0]
        self.pool.get('res.company').write(cr, uid, company_id, {'country_id': be_country_id})
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        res = super(wizard_multi_charts_accounts, self).execute(cr, uid, ids, context=ctx)

        obj_mod = self.pool.get('ir.module.module')
        obj_lang = self.pool.get('res.lang')
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

        chart_template = obj_multi.chart_template_id
        chart_template_root = chart_template
        
        chart_templates = [chart_template]
        parent_chart = chart_template.parent_id
        while parent_chart:
            chart_templates.insert(0,parent_chart)
            chart_template_root = parent_chart
            parent_chart = parent_chart.parent_id
                        
        # load languages and copy translations
        langs = (obj_multi.load_nl_BE and ['nl_BE'] or []) + (obj_multi.load_fr_BE and ['fr_BE'] or []) + \
            (obj_multi.load_nl_NL and ['nl_NL'] or []) + (obj_multi.load_fr_FR and ['fr_FR'] or [])
        if langs and obj_multi.multilang_be:
            installed_mids = obj_mod.search(cr, uid, [('state', '=', 'installed')])
            for lang in langs:
                lang_ids = obj_lang.search(cr, uid, [('code','=', lang)])
                if not lang_ids:
                    obj_mod.update_translations(cr, uid, installed_mids, lang)
       
            # copy account.account translations
            in_field = 'name'
            acc_root_id = obj_acc.search(cr, uid, [('company_id', '=', company_id), ('parent_id', '=', None)])[0]                       
            in_ids = []
            for template in chart_templates:
                children_acc_criteria = [('chart_template_id','=', template.id)]
                if template.account_root_id.id:
                    children_acc_criteria = ['|'] + children_acc_criteria + ['&',('parent_id','child_of', [template.account_root_id.id]),('chart_template_id','=', False)]
                in_ids += obj_acc_template.search(cr, uid, [('nocreate','!=',True)] + children_acc_criteria, order='id')
            if in_ids:
                in_ids.pop(0)
                out_ids = obj_acc.search(cr, uid, [('id', 'child_of', [acc_root_id])], order='id')[1:]
                # remove accounts created outside the template copy process (e.g. bank accounts)
                if len(in_ids) <> len(out_ids):
                    diff = len(out_ids) - len(in_ids)
                    out_ids = out_ids[:-diff] 
                # Perform basic sanity check on in/out pairs to protect against changes in the 
                # process that generates accounts from templates
                for i in range(len(in_ids)):
                    in_acc = obj_acc_template.browse(cr, uid, in_ids[i])
                    out_acc = obj_acc.browse(cr, uid, out_ids[i])
                    if in_acc.code[0] != out_acc.code[0]:
                        raise orm.except_orm(_('Warning!'),
                             _('The generation of translations from the template for %s failed!'    \
                               '\nPlease report this issue via your OpenERP support channel.' % obj_acc._name))
                self.copy_xlat(cr, uid, langs, obj_acc_template, in_field, in_ids, obj_acc, out_ids)
                acc_template_ids = in_ids # cf. infra : creation of bank accounts
            
            # copy account.tax.code translations
            in_field = 'name' 
            tax_code_template_root_id = chart_template_root.tax_code_root_id.id                    
            tax_code_root_id = obj_tax_code.search(cr, uid, [('company_id', '=', company_id), ('parent_id', '=', None)])[0]  
            in_ids = obj_tax_code_template.search(cr, uid, [('id', 'child_of', [tax_code_template_root_id])], order='id')[1:]
            if in_ids:
                out_ids = obj_tax_code.search(cr, uid, [('id', 'child_of', [tax_code_root_id])], order='id')[1:]
                # Perform basic sanity check on in/out pairs to protect against changes in the 
                # process that generates tax codes from templates
                for i in range(len(in_ids)):
                    in_tax_code = obj_tax_code_template.browse(cr, uid, in_ids[i])
                    out_tax_code = obj_tax_code.browse(cr, uid, out_ids[i])
                    if in_tax_code.name[0] != out_tax_code.name[0]:
                        raise orm.except_orm(_('Warning!'),
                             _('The generation of translations from the template for %s failed!'    \
                               '\nPlease report this issue via your OpenERP support channel.' % obj_tax_code._name))
                self.copy_xlat(cr, uid, langs, obj_tax_code_template, in_field, in_ids, obj_tax_code, out_ids)
            
            # copy account.tax translations
            if obj_multi.complete_tax_set: # skip xlats from templates in case tax rates (and hence naming) can be modified via setup wizard
                in_field = 'name' 
                in_ids = []
                for template in chart_templates:
                    in_ids += sorted([x.id for x in template.tax_template_ids])
                if in_ids:
                    out_ids = obj_tax.search(cr, uid, [('company_id', '=', company_id)], order='id')
                    # Perform basic sanity check on in/out pairs to protect against changes in the 
                    # process that generates tax objects from templates
                    for i in range(len(in_ids)):
                        in_tax = obj_tax_template.browse(cr, uid, in_ids[i])
                        out_tax = obj_tax.browse(cr, uid, out_ids[i])
                        if in_tax.name[0] != out_tax.name[0]:
                            raise orm.except_orm(_('Warning!'),
                                 _('The generation of translations from the template for %s failed!'    \
                                   '\nPlease report this issue via your OpenERP support channel.' % obj_tax._name))
                    self.copy_xlat(cr, uid, langs, obj_tax_template, in_field, in_ids, obj_tax, out_ids)
           
            # copy account.fiscal.position note field
            in_ids = []
            for template in chart_templates:
                in_ids += obj_fiscal_position_template.search(cr, uid, [('chart_template_id', '=', template.id)], order='id')
            if in_ids:
                out_ids = obj_fiscal_position.search(cr, uid, [('company_id', '=', company_id)], order='id')
                # Perform basic sanity check on in/out pairs to protect against changes in the 
                # process that generates fiscal positions from templates
                for i in range(len(in_ids)):
                    in_fp = obj_fiscal_position_template.browse(cr, uid, in_ids[i])
                    out_fp = obj_fiscal_position.browse(cr, uid, out_ids[i])
                    if in_fp.name[0] != out_fp.name[0]:
                        raise orm.except_orm(_('Warning!'),
                             _('The generation of translations from the template for %s failed!'    \
                               '\nPlease report this issue via your OpenERP support channel.' % obj_fiscal_position._name))
                for i in range(len(in_ids)):
                    fp_note = obj_fiscal_position_template.read(cr, uid, in_ids[i], ['note'])
                    fp_note = fp_note['note']
                    if fp_note:
                        obj_fiscal_position.write(cr, uid, out_ids[i], {'note': fp_note})
                # copy account.fiscal.position translations
                in_fields = ['name', 'note']
                for in_field in in_fields:
                    self.copy_xlat(cr, uid, langs, obj_fiscal_position_template, in_field, in_ids, obj_fiscal_position, out_ids)       
           
        return res

    def _get_load_BE(self, cr, uid, context=None):
        if context and context.get('lang'):
            if context['lang'] in ['nl_NL', 'fr_FR']:
                return False
        return True        

    def _get_load_noBE(self, cr, uid, context=None):
        if context and context.get('lang'):
            if context['lang'] in ['nl_NL', 'fr_FR']:
                return True
        return False

    _columns = {
        'load_nl_BE': fields.boolean('Load Dutch (nl_BE) Translation'),
        'load_fr_BE': fields.boolean('Load French (fr_BE) Translation'),        
        'load_nl_NL': fields.boolean('Load Dutch (nl_NL) Translation'),
        'load_fr_FR': fields.boolean('Load French (fr_FR) Translation'),        
        'multilang_be':fields.boolean('Multilang Belgian CoA'),
    }
    _defaults = {
        'load_nl_BE' : _get_load_BE,
        'load_fr_BE' : _get_load_BE,        
        'load_nl_NL' : _get_load_noBE,        
        'load_fr_FR' : _get_load_noBE,        
        'multilang_be': False,
    }
