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

from openerp.osv import fields, orm
from openerp.tools.translate import _
#import logging
#_logger = logging.getLogger(__name__)


class be_legal_financial_reportscheme(orm.Model):
    _name = 'be.legal.financial.reportscheme'
    _description = 'Belgian Legal Financial Report Scheme (Full)'
    _rec_name = 'account_group'
    _order = 'account_group'
    _columns = {
        'account_group': fields.char('Group', size=4, help='General Account Starting Digits'),
        'report_id': fields.many2one('account.financial.report', 'Report Entry', ondelete='cascade'),
        'account_ids': fields.related('report_id','account_ids', type='one2many', relation='account.account', string='Accounts', readonly=True),
    }
    _sql_constraints = [
        ('group_uniq', 'unique (account_group)', 'The General Account Group must be unique !')
    ]    


class account_financial_report(orm.Model):
    _inherit = 'account.financial.report'
    _columns = {    
        'code': fields.char('Code', size=16),
        'invisible': fields.boolean('Invisible', help="Hide this entry from the printed report."),
    }

    def _get_children_by_order(self, cr, uid, ids, context=None):
        res = []
        if context.get('get_children_by_sequence'):
            res = self.search(cr, uid, [('id', 'child_of', ids[0]), ('invisible', '=', 0)], order='sequence ASC', context=context)
        else:
            for id in ids:
                res.append(id)
                ids2 = self.search(cr, uid, [('parent_id', '=', id), ('invisible', '=', 0)], order='sequence ASC', context=context)
                res += self._get_children_by_order(cr, uid, ids2, context=context)
        return res

    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        #_logger.warn('read, context = %s', context)
        res = super(account_financial_report, self).read(cr, user, ids, fields, context, load)
        context = context or {}
        if 'name' in fields:
            for entry in res:
                if entry.get('code') and context.get('code_print'):
                    entry['name'] = entry['name'] + ' - (' + entry['code'] + ')' 
        return res


class account_account(orm.Model):
    _inherit = 'account.account'

    _columns = {
        'centralized': fields.boolean('Centralized', 
            help="this flag has an effect on the following reports:\n" \
                 "- Belgian legal BNB report : a 'centralized' account of type 'view' can be used as a substitute for its children (e.g. create a '400000' of type view whereby the children are of type 'receivable'\n" \
                 "- General Ledger report (the webkit one only), no details will be displayed in the General Ledger report (the webkit one only), only centralized amounts per period.")
    }
    _defaults = {
        'centralized': False,
    }

    """
    _be_scheme_countries : 
        override this attribute with the list of countries for which you want to use the Belgian BNB scheme 
        for financial reporting purposes
    """
    _be_scheme_countries = ['BE']

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """ improve performance of _update_be_reportscheme method """
        #_logger.warn('%s, search, args=%s, context=%s', self._name, args, context)
        if context is None: context = {}
        if context.get('update_be_reportscheme'):
            be_scheme_company_ids = []
            company_obj = self.pool.get('res.company')
            company_ids = company_obj.search(cr, uid, [])
            for company_id in company_ids:
                company = company_obj.browse(cr, uid, company_id)
                if company.country_id.code in self._be_scheme_countries:
                    be_scheme_company_ids.append(company_id)
            args += [('company_id', 'in', be_scheme_company_ids)]
        #_logger.warn('%s, search, args=%s', self._name, args)
        return super(account_account, self).search(cr, uid, args, offset, limit, order, context, count)

    def create(self, cr, uid, vals, context=None):
        acc_id = super(account_account, self).create(cr, uid, vals, context=context) 
        #_logger.warn('create, vals = %s, context = %s', vals, context)
        scheme_obj = self.pool.get('be.legal.financial.reportscheme')
        scheme_table = scheme_obj.read(cr, uid, scheme_obj.search(cr, uid, []), ['account_group', 'report_id'], context=context)
        be_report_ids = [x['report_id'][0] for x in scheme_table]
        acc_code = vals['code']
        account = self.browse(cr, uid, acc_id)
        if account.type not in ['view', 'consolidation'] and account.company_id.country_id.code in self._be_scheme_countries:
            be_report_entries =  filter(lambda x: acc_code[0:len(x['account_group'])] == x['account_group'], scheme_table)
            if be_report_entries:
                if len(be_report_entries) > 1:
                    raise orm.except_orm(_('Configuration Error !'), _('Configuration Error in the Belgian Legal Financial Report Scheme.'))
                be_report_id = be_report_entries[0]['report_id'][0]
                self.write(cr, uid, account.id, {'financial_report_ids': [(4, be_report_id)]})
        return acc_id

    def write(self, cr, uid, ids, vals, context=None):
        #_logger.warn('%s, write, ids=%s, vals = %s, context = %s', self._name, ids, vals, context)
        if context is None: context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        vals_in = vals.copy()
        if 'code' in vals.keys() or 'type' in vals.keys():
            scheme_obj = self.pool.get('be.legal.financial.reportscheme')
            scheme_table = scheme_obj.read(cr, uid, scheme_obj.search(cr, uid, []), ['account_group', 'report_id'], context=context)
            be_report_ids = [x['report_id'][0] for x in scheme_table]
            acc_code = vals.get('code')
            acc_type = vals.get('type')
            centralized = vals.get('centralized')
            for account in self.browse(cr, uid, ids):
                updated = False
                if account.company_id.country_id.code in self._be_scheme_countries:
                    acc_code = acc_code or account.code
                    acc_type = acc_type or account.type
                    centralized = centralized or account.centralized
                    be_report_entries =  filter(lambda x: acc_code[0:len(x['account_group'])] == x['account_group'], scheme_table)
                    if len(be_report_entries) > 1:
                        raise orm.except_orm(_('Configuration Error !'), _('Configuration Error in the Belgian Legal Financial Report Scheme.'))                       
                    be_report_id = be_report_entries and be_report_entries[0]['report_id'][0]
                    for fin_report in account.financial_report_ids:
                        if fin_report.id in be_report_ids:
                            if acc_type not in ['view', 'consolidation'] and fin_report.id == be_report_id:
                                updated = True
                            elif acc_type == 'view' and centralized and fin_report.id == be_report_id:
                                updated = True   
                            else:
                                vals.update({'financial_report_ids': [(3, fin_report.id)]})
                                updated = True
                    if be_report_id and (acc_type not in ['view', 'consolidation'] or (acc_type == 'view' and centralized)) and not updated:
                        vals.update({'financial_report_ids': [(4, be_report_id)]})
        return super(account_account, self).write(cr, uid, ids, vals, context=context)


class l10n_be_update_be_reportscheme(orm.TransientModel):
    _name = 'l10n_be.update_be_reportscheme'
    _description = 'Update BNB/NBB financial reports configuration'
    
    _columns = {
        'note':fields.text('Result', readonly=True),
    }
    
    def update_be_reportscheme(self, cr, uid, ids=None, context=None):
        """" 
        This method is executed when installing the module and will create/update
        the entries in the BNB/NBB legal report scheme. 
        """
        note = ''
        upd_ctx = {'update_be_reportscheme': True}
        mod_obj = self.pool.get('ir.model.data')
        acc_obj = self.pool.get('account.account')
        scheme_obj = self.pool.get('be.legal.financial.reportscheme')
        scheme_table = scheme_obj.read(cr, uid, scheme_obj.search(cr, uid, []), ['account_group', 'report_id'], context=context)
        be_report_ids = [x['report_id'][0] for x in scheme_table]
        account_ids = acc_obj.search(cr, uid, ['|',('type', '!=', 'view'),'&',('type', '=', 'view'), ('centralized', '=', True)], context=upd_ctx)
        accounts = acc_obj.read(cr, uid, account_ids, ['code', 'type', 'centralized', 'company_id'], context=context)

        # delete old reporting configuration
        cr.execute(
            "DELETE FROM account_account_financial_report "
            "WHERE report_line_id IN %s and account_id IN %s", 
            (tuple(be_report_ids), tuple(account_ids)))

        # filter out children of centralized accounts
        centralized_accounts = filter(lambda x: x['centralized'] and x['type'] == 'view', accounts)
        remove_ids = []
        for ca in centralized_accounts:
            ca_children = acc_obj.browse(cr, uid, ca['id'], context=context).child_id
            config_errors = filter(lambda x: x.centralized, ca_children)
            if config_errors:
                note += _("Configuration Error :\n\n")
                note += _("A centralized account that is a child of a parent centralized account is not supported !\n" \
                          "Please review the configuration settings of the following account(s) and its parents: \n%s") %(', '.join([x.code + ' - ' + x.name + ' ('+ x.company_id.name + ')'  for x in config_errors]))
                self.write(cr, uid, ids[0], {'note': note})
                model, res_id = mod_obj.get_object_reference(cr, uid, 'l10n_be_coa_multilang', 'update_be_reportscheme_result_view')
                return {
                    'name': _('Results'),
                    'res_id': ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'l10n_be.update_be_reportscheme',
                    'view_id': False,
                    'target': 'new',
                    'views': [(res_id, 'form')],
                    'type': 'ir.actions.act_window',                        
                  }
            remove_ids += [x.id for x in ca_children]
        accounts = filter(lambda x: x['id'] not in remove_ids, accounts)

        # filter out accounts that do not belong to a reporting group 
        be_scheme_accounts = []
        for account in accounts:
            for entry in scheme_table:
                if account['code'][0:len(entry['account_group'])] == entry['account_group']:
                    be_scheme_accounts.append(account)
                    break

        # write list of entries that are not included in the BNB reports to the note field
        non_be_scheme_account_ids =  set([x['id'] for x in accounts]) - set([x['id'] for x in be_scheme_accounts])
        if non_be_scheme_account_ids:
            note += _("Following accounts are not included in the legal Belgian Balance and P&L reports:\n\n")
            for a_id in non_be_scheme_account_ids:
                a = acc_obj.browse(cr, uid, a_id, context=context)
                note += "Code: %s (id: %s), company: %s\n" %(a.code, a_id, a.company_id.name)
                #self.log(cr, uid, a_id, "Account '%s' (id: %s), company '%s' is not included in the legal Belgian Balance and P&L reports." %(a.code, a_id, a.company_id.name))
            note += "\n"

        for account in be_scheme_accounts:          
            be_report_entries = filter(lambda x: account['code'][0:len(x['account_group'])] == x['account_group'], scheme_table)
            if len(be_report_entries) > 1:
                raise orm.except_orm(_('Configuration Error !'), _('Configuration Error in the Belgian Legal Financial Report Scheme.'))                       
            be_report_id = be_report_entries and be_report_entries[0]['report_id'][0]
            acc_obj.write(cr, uid, account['id'], {'financial_report_ids': [(4, be_report_id)]})

        if note:
            self.write(cr, uid, ids[0], {'note': note})
            model, res_id = mod_obj.get_object_reference(cr, uid, 'l10n_be_coa_multilang', 'update_be_reportscheme_result_view')
            return {
                'name': _('Results'),
                'res_id': ids[0],
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'l10n_be.update_be_reportscheme',
                'view_id': False,
                'target': 'new',
                'views': [(res_id, 'form')],
                'type': 'ir.actions.act_window',                        
              }
        else:
            return {'type': 'ir.actions.act_window_close'}
