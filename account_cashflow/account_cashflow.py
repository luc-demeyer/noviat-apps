# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2012 Noviat nv/sa (www.noviat.be). All rights reserved.
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
from datetime import datetime, date, timedelta
import tools
from osv import osv, fields
import decimal_precision as dp
from lxml import etree
import logging
_logger = logging.getLogger(__name__)
from tools.translate import _

class account_cashflow_code(osv.osv):  
    _name = 'account.cashflow.code'
    _description = 'Cash Flow Code'
    _order = 'sequence,type desc,code'
    
    def format_date(self, cr, uid, date, context):
        ''' format date according to language from context '''
        if not context:
            return date
        lang = context.get('lang')
        lang_obj = self.pool.get('res.lang')
        lang_id = lang_obj.search(cr, uid, [('code','=',lang)])[0]
        date_format = str(lang_obj.browse(cr, uid, lang_id).date_format)
        return date.strftime(date_format)

    def _balance_period(self, cr, uid, ids, field_name=None, arg=None, context=None, date_start=None, date_stop=None, day=None):
        if context is None:
            context = {}
        if not date_start:
            date_start = context.get('date_start', None)
        if not date_stop:
            date_stop = context.get('date_stop', None)
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        journal_ids = context.get('journal_ids')

        if day:
            date_start = day        
            cr.execute('SELECT cashflow_code_id, sum(balance) FROM account_cashflow_balance ' \
                'WHERE date = %s AND journal_id IN %s GROUP BY cashflow_code_id', 
                (day, tuple(journal_ids)))
        elif date_start:
            cr.execute('SELECT cashflow_code_id, sum(balance) FROM account_cashflow_balance ' \
                'WHERE date >= %s AND date <= %s AND journal_id IN %s GROUP BY cashflow_code_id',
                (date_start, date_stop, tuple(journal_ids)))            
        else:
            cr.execute('SELECT id, 0.0 as amount FROM account_cashflow_code ')
        balances = dict(cr.fetchall())
        # add 'init' balance
        balance_init_id = context.get('balance_init_id', None)
        if date_start:
            balopen_obj = self.pool.get('account.cashflow.opening.balance')
            balance_init = {balance_init_id: balopen_obj.calc_opening_balance(cr, uid, date_start, balance_init_id, journal_ids)}
        else:
            balance_init = {balance_init_id: 0.0}
        balances.update(balance_init)
        # calculate period balances
        digits = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        period_balances = {}
        def _rec_get(record):
            amount = balances.get(record.id, 0.0)
            for rec in record.child_ids:
                amount += _rec_get(rec) * rec.parent_sign
            return amount
        for record in self.browse(cr, uid, ids, context=context):
            period_balances[record.id] = round(_rec_get(record), digits)
        return period_balances

    def _balance_day(self, cr, uid, ids, field_name, arg, context):
        if context is None:
            context = {}
        day = None
        if context.get('date_start', None):
            date_start = context.get('date_start')
            nbr_days = int(context.get('nbr_days'))
            x = int(field_name[-2:])
            if x == 1:
                day = date_start                
            elif x <= nbr_days:
                day = (datetime.strptime(date_start, '%Y-%m-%d').date() + timedelta(days = int(field_name[-2:])-1)).isoformat()
        return self._balance_period(cr, uid, ids, field_name, arg, context, day=day)


    def fields_get(self, cr, uid, fields=None, context=None):
        res = super(account_cashflow_code, self).fields_get(cr, uid, fields, context)
        # remove type='provision' from selection list when configuring Cash Flow Codes
        if context.get('manage_cfc') and res.get('type'):
            res['type']['selection'].remove(('provision', u'Provision'))
        # rename date fields
        format_date = self.format_date
        if context.has_key('date_start'):
            date_start = datetime.strptime(context.get('date_start'), '%Y-%m-%d').date()            
            nbr_days = int(context.get('nbr_days'))
            days = [format_date(cr, uid, date_start, context)] + [format_date(cr, uid, date_start + timedelta(days=x), context) for x in range(1, nbr_days)]        
            for x in range(1, nbr_days + 1):
                if x < 10:
                    field = 'balance_day0' + str(x)
                else:
                    field = 'balance_day' + str(x)
                if res.get(field, None):
                    res[field]['string'] = days[x-1]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_cashflow_code, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if context.has_key('nbr_days') and view_type=='tree':
            view_obj = etree.XML(res['arch'])
            nbr_days = int(context.get('nbr_days'))        
            for el in view_obj:
                if 'balance_day' in el.get('name'):
                    day = int(el.get('name')[11:])
                    if day > nbr_days:
                        el.getparent().remove(el)               
                res['arch'] = etree.tostring(view_obj)        
        return res

    _columns = {
        'name': fields.char('Description', size=128, required=True, translate=False), # translate True not supported (would require changes to sync twin xlats)
        'code': fields.char('Code', size=16, required=True),
        'type': fields.selection([
            ('view', 'View'),
            ('normal', 'Normal'),
            ('provision', 'Provision'),            
            ('init', 'Init'), 
        ], 'Type', required=True,
            help="Please ensure to have exactly one code of type 'Init' as placeholder for the Initial Balance."),
        'twin_id': fields.many2one('account.cashflow.code', 'Twin Code', domain=[('type','in',['normal', 'provision'])], ondelete='cascade',
            help="Twin code to reconcile provision lines with transaction lines."),
        'sequence': fields.integer('Sequence', required=True),        
        'balance_period': fields.function(_balance_period, method=True, string='Period Balance',
            help='Balance of the transactions over the selected period. The Valuta Date is used to calculate the balance'),

        'balance_day01': fields.function(_balance_day, method=True, string='Day 1'),
        'balance_day02': fields.function(_balance_day, method=True, string='Day 2'),
        'balance_day03': fields.function(_balance_day, method=True, string='Day 3'),
        'balance_day04': fields.function(_balance_day, method=True, string='Day 4'),
        'balance_day05': fields.function(_balance_day, method=True, string='Day 5'),
        'balance_day06': fields.function(_balance_day, method=True, string='Day 6'),
        'balance_day07': fields.function(_balance_day, method=True, string='Day 7'),

        'balance_day08': fields.function(_balance_day, method=True, string='Day 8'),
        'balance_day09': fields.function(_balance_day, method=True, string='Day 9'),
        'balance_day10': fields.function(_balance_day, method=True, string='Day 10'),
        'balance_day11': fields.function(_balance_day, method=True, string='Day 11'),
        'balance_day12': fields.function(_balance_day, method=True, string='Day 12'),
        'balance_day13': fields.function(_balance_day, method=True, string='Day 13'),
        'balance_day14': fields.function(_balance_day, method=True, string='Day 14'),

        'balance_day15': fields.function(_balance_day, method=True, string='Day 15'),
        'balance_day16': fields.function(_balance_day, method=True, string='Day 16'),
        'balance_day17': fields.function(_balance_day, method=True, string='Day 17'),
        'balance_day18': fields.function(_balance_day, method=True, string='Day 18'),
        'balance_day19': fields.function(_balance_day, method=True, string='Day 19'),
        'balance_day20': fields.function(_balance_day, method=True, string='Day 20'),
        'balance_day21': fields.function(_balance_day, method=True, string='Day 21'),

        'balance_day22': fields.function(_balance_day, method=True, string='Day 22'),
        'balance_day23': fields.function(_balance_day, method=True, string='Day 23'),
        'balance_day24': fields.function(_balance_day, method=True, string='Day 24'),
        'balance_day25': fields.function(_balance_day, method=True, string='Day 25'),
        'balance_day26': fields.function(_balance_day, method=True, string='Day 26'),
        'balance_day27': fields.function(_balance_day, method=True, string='Day 27'),
        'balance_day28': fields.function(_balance_day, method=True, string='Day 28'),

        'balance_day29': fields.function(_balance_day, method=True, string='Day 29'),
        'balance_day30': fields.function(_balance_day, method=True, string='Day 30'),
        'balance_day31': fields.function(_balance_day, method=True, string='Day 31'),
        'balance_day32': fields.function(_balance_day, method=True, string='Day 32'),
        'balance_day33': fields.function(_balance_day, method=True, string='Day 33'),
        'balance_day34': fields.function(_balance_day, method=True, string='Day 34'),
        'balance_day35': fields.function(_balance_day, method=True, string='Day 35'),

        'balance_day36': fields.function(_balance_day, method=True, string='Day 36'),
        'balance_day37': fields.function(_balance_day, method=True, string='Day 37'),
        'balance_day38': fields.function(_balance_day, method=True, string='Day 38'),
        'balance_day39': fields.function(_balance_day, method=True, string='Day 39'),
        'balance_day40': fields.function(_balance_day, method=True, string='Day 40'),
        'balance_day41': fields.function(_balance_day, method=True, string='Day 41'),
        'balance_day42': fields.function(_balance_day, method=True, string='Day 42'),

        'parent_id': fields.many2one('account.cashflow.code', 'Parent Code', domain=[('type', '=', 'view')]),
        'child_ids': fields.one2many('account.cashflow.code', 'parent_id', 'Child Codes'),
        'st_line_ids': fields.one2many('account.cashflow.line', 'cashflow_code_id', 'Bank Statement Lines'),
        'parent_sign': fields.float('Multiplier for Parent Code', required=True, 
            help='You can specify here the coefficient that will be used when consolidating the amount of this code into its parent. Set this value to 1 except for the top level Cash FLow Codes (Company and Total Balance).'),
        'active': fields.boolean('Active'),
        'company_id': fields.many2one('res.company', 'Company', required=True),   
    }
    _defaults = {
        'active': True,
        'type': 'normal',
        'parent_sign': 1.0,         
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    _sql_constraints = [
        ('code_company_uniq', 'unique (code, type, company_id)', 'The code must be unique per company !'),
    ]

    def _check_type_init(self, cr, uid, ids):
        for cfc in self.browse(cr, uid, ids):
            if cfc.type == 'init':
                init_ids = self.search(cr, uid, [('type', '=', 'init'), ('company_id', '=', cfc.company_id.id)])
                if len(init_ids) > 1:
                    return False
        return True

    _constraints = [
        (_check_type_init, '\n\n' + "You can only have one code of type 'Init' per Company !", ['type']),
        ]

    def onchange_parent_id(self, cr, uid, ids, parent_id, context=None):
        parent = self.browse(cr, uid, parent_id, context=context)
        return {'value': {'sequence': parent.sequence}}

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            if context.get('cashflow_code_name_get', False) == 'code':
                name = record['code']
            else:
                name = record['code'] + ' ' + record['name']
            res.append((record['id'], name))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = []
        if name:
            ids = self.search(cr, user, [('code', operator, name + '%')] + args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit)
            if not ids and len(name.split()) >= 2:
                #Separating code and name for searching
                operand1, operand2 = name.split(' ', 1) #name can contain spaces
                ids = self.search(cr, user, [('code', '=like', operand1), ('name', operator, operand2)] + args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        elif context.get('search_origin') in ['account.cashflow.line.overview', 'assign.cashflow.code.all.line']:
            # do not override search args when called from 'account.cashflow.line.overview'
            pass
        elif context.has_key('date_start'):
            # remove empty lines when called from Cash Flow Chart
            move_cfc_ids = self.search(cr, uid, [('type', 'not in', ['normal', 'provision'])])
            cr.execute('SELECT b.cashflow_code_id, min(b.balance), max(b.balance) FROM account_cashflow_balance b ' \
                'INNER JOIN account_cashflow_code c on b.cashflow_code_id=c.id ' \
                'WHERE b.date >= %s AND b.date <= %s AND c.type IN (\'normal\',\'provision\') AND c.active = TRUE ' \
                'GROUP BY cashflow_code_id',
                (context['date_start'], context['date_stop']))  
            res=cr.dictfetchall()
            for cfc in res:
                if not (cfc['min'] == cfc['max'] == 0.0): 
                    move_cfc_ids += [cfc['cashflow_code_id']]
            args += [('id', 'in', move_cfc_ids)]
        return super(account_cashflow_code, self).search(cr, uid, args, offset, limit, order, context, count)
    
    def copy(self, cr, uid, id, default=None, context=None):
        #_logger.warn(self._name + ', def copy, id=%s, default=%s, context=%s', id, default, context)
        if context is None:
            context={}
        if not context.get('create_cfc_twin'):
            cfc = self.browse(cr, uid, id, context=context)
            if not default:
                default = {}
            default = default.copy()
            default.update({
                'st_line_ids': [],
                'child_ids':[],
                })
            default['code'] = cfc.code + ' (copy)'
        return super(account_cashflow_code, self).copy(cr, uid, id, default, context)
    
    def create(self, cr, uid, vals, context=None):
        #_logger.warn(self._name + ', def create, vals=%s, context=%s', vals, context)
        if context is None:
            context = {}
        err_string = "Invalid Cash Flow Code Configuration. \
            \nPlease contact info@noviat.be for support on this issue. \
            \n\naccount.cashflow.code, create, error code %s."
        res_id = super(account_cashflow_code, self).create(cr, uid, vals, context=context)
        cfc_type = vals.get('type')
        if cfc_type == 'normal' and not context.get('create_cfc_twin'):
            twin_vals = vals.copy()
            twin_vals['type'] = 'provision'
            twin_vals['twin_id'] = res_id
            twin_id = self.create(cr, uid, twin_vals, context={'create_cfc_twin': 1})
            if not twin_id:
                raise osv.except_osv('Error', err_string %'001')
            self.write(cr, uid, [res_id], {'twin_id': twin_id}, context={'create_cfc_twin': 1})
        return res_id

    def write(self, cr, uid, ids, vals, context={}):
        #_logger.warn(self._name + ', def write, ids=%s, vals=%s, context=%s', ids, vals, context)
        if context is None:
            context={}
        err_string = "Invalid Cash Flow Code Configuration. \
            \nPlease contact info@noviat.be for support on this issue. \
            \n\naccount.cashflow.code, write, error code %s."
        unlink_ids = []
        for cfc in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            if not context.get('create_cfc_twin') and not context.get('update_cfc_twin'):
                old_type = cfc.type
                new_type = vals.get('type') or old_type
                twin_id = cfc.twin_id
                twin_vals = vals.copy()
                if old_type == 'init':
                    if new_type != old_type:
                        raise osv.except_osv('Warning', _("Operation not allowed ! \
                            You cannot modify a Cash Flow Code of type 'Init'."))
                elif old_type == 'view':
                    if new_type == 'normal':
                        if cfc.child_ids:
                            raise osv.except_osv('Warning', _("Operation not allowed.\
                                \nPlease change first the Parent Code of the following Childs: %s.") \
                                %(','.join(list(set([x.code for x in cfc.child_ids])))))
                        # create/sync twin record                   
                        twin_vals.update({
                            'type': 'provision',
                            'code': cfc.code,
                            'twin_id': cfc.id,
                            })
                        ctx.update({'create_cfc_twin': 1})
                        twin_id = self.copy(cr, uid, cfc.id, twin_vals, context=ctx)
                        vals['twin_id'] = twin_id
                elif old_type == 'normal':
                    if new_type in ['view', 'init']:
                        vals['twin_id'] = None
                        unlink_ids.append(twin_id.id)
                    elif new_type == 'normal':
                        # sync twin record                       
                        twin_vals.update({
                            'type': 'provision',
                            'twin_id': cfc.id,
                            })
                        self.write(cr, uid, [cfc.twin_id.id], twin_vals, context={'update_cfc_twin': 1})
                    else:
                        raise osv.except_osv('Error', err_string %'002')
                else:
                    raise osv.except_osv('Error', err_string %'003')
            super(account_cashflow_code, self).write(cr, uid, cfc.id, vals, context=ctx)
        if unlink_ids:
            self.unlink(cr, uid, unlink_ids)
        return True

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        err_string = "Invalid Cash Flow Code Configuration. \
            \nPlease contact info@noviat.be for support on this issue. \
            \n\naccount.cashflow.code, unlink, error code %s."
        for cfc in self.browse(cr, uid, ids, context):  
            if cfc.type == 'normal':
                twin_id = cfc.twin_id
                if not twin_id:
                    raise osv.except_osv('Error', err_string %'001')
                ids.append(twin_id.id)
            elif cfc.type == 'init':
                raise osv.except_osv('Warning', _("Operation not allowed ! \
                    You cannot remove a Cash Flow Code of type 'Init'."))
        return super(account_cashflow_code, self).unlink(cr, uid, ids, context=context)
    
account_cashflow_code()

class account_cashflow_rule(osv.osv):
    _name = 'account.cashflow.rule'
    _description = 'Rules Engine to assign Cash Flow Codes'
    _order = 'sequence'
    _columns = {
        'name': fields.char('Rule Name', size=128, required=True),                
        'sequence': fields.integer('Sequence', help='Determines the order of the rules to assign Cash Flow Codes'),
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', required=True),
        'sign': fields.selection([
            ('debit', 'Debit (+)'),
            ('credit', 'Credit (-)'),
            ], 'Movement Sign',
            help='Sign for the Cash Flow Code Assignment'),
        'journal_id': fields.many2one('account.journal', 'Journal', ondelete='cascade',
            domain=[('type', 'in', ['bank', 'cash'])], required=True),
        'account_id': fields.many2one('account.account', 'Account', ondelete='cascade', domain=[('type', '!=', 'view')]),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'active': fields.boolean('Active', help='Switch off this rule.'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'active': True,                 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    def _check_journal_currency(self, cr, uid, ids):
        for rule in self.browse(cr, uid, ids):
            rule_currency = rule.journal_id.currency or rule.company_id.currency_id
            return rule_currency == rule.company_id.currency_id
        return True

    _constraints = [
        (_check_journal_currency, "\n\nFinancial Journals in Foreign Currency are not yet supported. \
            \nPlease contact info@noviat.be if you require this feature.", ['journal_id']),
        ]

    def cfc_id_get(self, cr, uid, sign=None, account_id=None, journal_id=None, partner_id=None, 
                   extra_fields={}, company_id=None, context=None):       
        """
        The extra_fields dictionary (extra_fields = {fieldname1: value1, field_name2: value2, ... )) 
        allows addition of customer specific criteria via inheritance:
        - add extra fields (fieldname1, fieldname2, ... ) to account.cashflow.rule;
        - add extra_fields to the context ('extra_fields': [ (fieldname1, value1, operand1), (fieldname2, value2, operand2), ... ] ) of the create() method of account.bank.statement.line.
        """
        extra_select = ''
        base_condition = '(not rule[1] or (sign == rule[1])) and (not rule[2] or (journal_id == rule[2])) ' \
            'and (not rule[3] or (account_id == rule[3])) and (not rule[4] or (partner_id == rule[4])) '
        index = 4        
        extra_condition = ''
        for x in extra_fields:
            extra_select += ', %s' % x[0]
            value = x[1]
            operand = x[2]
            index += 1
            if isinstance(value, str) or isinstance(value, unicode):
                extra_condition += "and (not rule[%s] or ('%s' %s rule[%s])) " % (index, value, operand, index)
            else:    
                extra_condition += "and (not rule[%s] or (%s %s rule[%s])) " % (index, value, operand, index)
        cr.execute('SELECT cashflow_code_id, sign, journal_id, account_id, partner_id%s ' \
            'FROM account_cashflow_rule ' \
            'WHERE active = TRUE AND company_id = %s ' \
            'ORDER BY sequence' % (extra_select, company_id)
        )
        rules = cr.fetchall()    
        cfc_id = None
        condition = base_condition + extra_condition
        for rule in rules:
            if eval(condition):
                cfc_id = rule[0]
                break
        return cfc_id

account_cashflow_rule()

class account_cashflow_provision_line(osv.osv):

    def _get_reference_model(self, cr, uid, context=None):
        res = [('account.invoice', 'Invoice / Credit Note')] 
        return res
    
    def _get_update_info(self, cr, uid, ids, field_names, arg=None, context=None):
        cr.execute('SELECT id, \
            CASE \
                WHEN pl.write_date IS NOT NULL THEN date(pl.write_date) \
                ELSE date(pl.create_date) \
            END AS update_date, \
            CASE \
                WHEN pl.write_uid IS NOT NULL THEN pl.write_uid \
                ELSE pl.create_uid \
            END AS update_by \
            FROM account_cashflow_provision_line pl \
            WHERE id IN %s', (tuple(ids),))
        infos = cr.fetchall()
        res = {}
        for i in infos:
            res[i[0]] = {'update_date':i[1], 'update_by': i[2]}
        return res

    _order = 'val_date desc, journal_id'
    _name = 'account.cashflow.provision.line'
    _description = 'Cash Flow Provision Line'    
    _columns = {
        # general fields
        'description': fields.char('Description', size=64, states={'confirm': [('readonly', True)]}),
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', required=True, 
            domain=[('type', '=', 'provision')], states={'confirm': [('readonly', True)]}),
        'date': fields.date('Entry Date', required=True, readonly=True),
        'state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirmed')],
            'State', required=True, readonly=True),    
        'update_date': fields.function(_get_update_info, string='Update Date', readonly=True, type='date', multi='get_update'),
        'update_by': fields.function(_get_update_info, string='Updated by', type='many2one', relation='res.users', multi='get_update'),
        'note': fields.text('Notes', states={'confirm': [('readonly', True)]}),
        # originating transaction fields
        'origin': fields.reference('Originating Transaction', size=128, readonly=True,
            selection=_get_reference_model,
            help='This field contains a reference to the transaction that originated the creation of this provision.'),
        # reconciliation lookup fields
        'journal_id': fields.many2one('account.journal', 'Journal', domain=[('type', '=', 'bank')], 
            states={'confirm': [('readonly', True)]}),
        'val_date': fields.date('Valuta Date', required=True, states={'confirm': [('readonly', True)]}),   
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), required=True, states={'confirm': [('readonly', True)]}),
        'partner_id': fields.many2one('res.partner', 'Partner', states={'confirm': [('readonly', True)]}),
        'name': fields.char('Communication', size=64, states={'confirm': [('readonly', True)]}),
        'payment_reference': fields.char('Payment Reference', size=35, states={'confirm': [('readonly', True)]},
            help="Payment Reference. For SEPA (SCT or SDD) transactions, the PaymentInformationIdentification " \
                 "is recorded in this field pertaining to a globalisation, and the EndToEndReference for " \
                 "simple transactions or for the details of a globalisation."),       
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
        # reconciliation result fields
        'cfc_normal_id': fields.related('cashflow_code_id', 'twin_id', type='many2one', 
            relation='account.cashflow.code', string='Reconcile Code', readonly=True),
        'type': fields.selection([
            ('supplier','Supplier'),
            ('customer','Customer'),
            ('general','General')
            ], 'Type', states={'confirm': [('readonly', True)]}),
        'account_id': fields.many2one('account.account','Account', domain=[('type', '<>', 'view')], 
            states={'confirm': [('readonly', True)]}),
        'cfline_partial_ids': fields.one2many('account.cashflow.line', 'cfpline_rec_partial_id', 'Partially Reconciled Cash Flow Lines'),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': 'draft',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    def write(self, cr, uid, ids, vals, context={}):
        cfbalance_obj = self.pool.get('account.cashflow.balance')        
        for pline in self.browse(cr, uid, ids, context):    
            # update account_cashflow_balance for changes on cashflow provision lines
            if vals.get('cashflow_code_id', False) or vals.get('val_date', False) or vals.get('amount', False):
                old_cfc_id = pline.cashflow_code_id.id or None
                new_cfc_id = vals.get('cashflow_code_id', old_cfc_id)
                old_val_date = pline.val_date
                new_val_date = vals.get('val_date', old_val_date)
                old_amount = pline.amount
                new_amount = vals.get('amount', old_amount)
                if old_cfc_id != new_cfc_id or old_val_date != new_val_date or old_amount != new_amount:
                    values = {
                        'old_cfc_id': old_cfc_id,
                        'new_cfc_id': new_cfc_id,
                        'old_val_date': old_val_date,
                        'new_val_date': new_val_date,
                        'old_amount': old_amount,                        
                        'new_amount': new_amount,
                    }
                    cfbalance_obj.update_balance(cr, uid, pline.journal_id.id, values)
        return super(account_cashflow_provision_line, self).write(cr, uid, ids, vals, context)       
     
    def create(self, cr, uid, vals, context=None):
        cfbalance_obj = self.pool.get('account.cashflow.balance')
        # update Cash Flow Balances table
        if vals.get('cashflow_code_id'): 
            values = {
                'old_cfc_id': False,
                'new_cfc_id': vals.get('cashflow_code_id'),
                'old_val_date': False,
                'new_val_date': vals.get('val_date'),
                'old_amount': False,
                'new_amount': vals['amount'],    
            }
            cfbalance_obj.update_balance(cr, uid, vals['journal_id'], values)
        return super(account_cashflow_provision_line, self).create(cr, uid, vals, context=context) 
    
    def unlink(self, cr, uid, ids, context=None):
        cfbalance_obj = self.pool.get('account.cashflow.balance')       
        for pline in self.browse(cr, uid, ids, context):  
            if pline.state == 'confirm':
                raise osv.except_osv('Warning', _('Delete operation not allowed !'))
            values = {
                'old_cfc_id': pline.cashflow_code_id.id,
                'new_cfc_id': False,
                'old_val_date': pline.val_date,
                'new_val_date': False,
                'old_amount': pline.amount,
                'new_amount': False,
            }
            cfbalance_obj.update_balance(cr, uid, pline.journal_id.id, values)   
        return super(account_cashflow_provision_line, self).unlink(cr, uid, ids, context=context)
         
account_cashflow_provision_line()

class account_cashflow_line(osv.osv):
    _name = 'account.cashflow.line'
    _description = 'Cash Flow Line'
    _inherits = {'account.bank.statement.line': 'st_line_id'}
    
    def _get_update_info(self, cr, uid, ids, field_names, arg=None, context=None):
        cr.execute('SELECT id, \
            CASE \
                WHEN sl_update_date > cl_update_date THEN date(sl_update_date) \
                ELSE date(cl_update_date) \
            END AS update_date, \
            CASE \
                WHEN sl_update_date > cl_update_date THEN sl_update_by \
                ELSE cl_update_by \
            END AS update_by \
            FROM \
                (SELECT cl.id, \
                    CASE \
                        WHEN sl.write_date IS NOT NULL THEN sl.write_date \
                        ELSE sl.create_date \
                    END AS sl_update_date, \
                    CASE \
                        WHEN sl.write_uid IS NOT NULL THEN sl.write_uid \
                        ELSE sl.create_uid \
                    END AS sl_update_by, \
                    CASE \
                        WHEN cl.write_date IS NOT NULL THEN cl.write_date \
                        ELSE cl.create_date \
                    END AS cl_update_date, \
                    CASE \
                        WHEN cl.write_uid IS NOT NULL THEN cl.write_uid \
                        ELSE cl.create_uid \
                    END AS cl_update_by \
                    FROM account_cashflow_line cl \
                    INNER JOIN account_bank_statement_line sl ON cl.st_line_id = sl.id \
                    WHERE cl.id IN %s) sq', (tuple(ids),))               
        infos = cr.fetchall()
        res = {}
        for i in infos:
            res[i[0]] = {'update_date':i[1], 'update_by': i[2]}
        return res
    
    _columns = {
        'st_line_id': fields.many2one('account.bank.statement.line', 'Bank Statement Line', ondelete='cascade', 
            required=True, states={'confirm': [('readonly', True)]}),
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', 
            domain=[('type', '=', 'normal')], states={'confirm': [('readonly', True)]}),
        'cfpline_rec_partial_id': fields.many2one('account.cashflow.provision.line', 'Partially Reconciled Provision Line', readonly=True, ondelete='set null'),
        'update_date': fields.function(_get_update_info, string='Update Date', readonly=True, type='date', multi='get_update'),
        'update_by': fields.function(_get_update_info, string='Updated by', type='many2one', relation='res.users', multi='get_update'),
        'journal_id': fields.related('st_line_id', 'journal_id', type='many2one', relation='account.journal', string='Journal', readonly=True),
    }

    def onchange_type(self, cr, uid, line_id, partner_id, type, context=None):
        return self.pool.get('account.bank.statement.line').onchange_type(cr, uid, line_id, partner_id, type, context=None)

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        return self.pool.get('account.bank.statement.line').onchange_partner_id(cr, uid, ids, partner_id, context=None)

    def write(self, cr, uid, ids, vals, context={}):
        cfbalance_obj = self.pool.get('account.cashflow.balance')
        for cfline in self.browse(cr, uid, ids, context):    
            old_cfc_id = cfline.cashflow_code_id.id or False
            # update embedded account.bank.statement.line first via super().write
            # changes to val_date and amount will result in updated balances via the write method of the embedded object
            super(account_cashflow_line, self).write(cr, uid, cfline.id, vals, context) 
            # update account_cashflow_balance
            if vals.has_key('cashflow_code_id'):
                new_cfc_id = vals['cashflow_code_id']
                if old_cfc_id != new_cfc_id:
                    values = {
                        'old_cfc_id': old_cfc_id,
                        'new_cfc_id': new_cfc_id,
                        'old_val_date': cfline.val_date,
                        'new_val_date': cfline.val_date,
                        'old_amount': cfline.amount,                        
                        'new_amount': cfline.amount,
                    }
                    cfbalance_obj.update_balance(cr, uid, cfline.journal_id.id, values)
        return True

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context.get('block_cashflow_line_delete', False):
            raise osv.except_osv('Warning', _('Delete operation not allowed ! \
                Please go to the associated bank statement in order to delete and/or modify this line'))
        return super(account_cashflow_line, self).unlink(cr, uid, ids, context=context)
   
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('active_model', False) == 'account.cashflow.code':
            cfc_obj = self.pool.get('account.cashflow.code')
            cfc_id = context.get('active_id', 0)
            cfc = cfc_obj.browse(cr, uid, cfc_id, context=context)
            def _ids_get(record):
                ids = [record.id]
                if record.type == 'view':
                    for child in record.child_ids:
                        ids += _ids_get(child)
                return ids
            cfc_ids = _ids_get(cfc)
            date_start = context.get('date_start', time.strftime('%Y-%m-%d'))
            date_stop = context.get('date_stop', time.strftime('%Y-%m-%d'))
            args += [('cashflow_code_id', 'in', cfc_ids), ('val_date', '>=', date_start), ('val_date', '<=', date_stop) ]
        return super(account_cashflow_line, self).search(cr, uid, args, offset, limit, order, context, count)   

    def view_header_get(self, cr, uid, view_id, view_type, context=None):
        if context is None:
            context = {}
        if context.get('active_model', False) == 'account.cashflow.code':
            format_date = self.pool.get('account.cashflow.code').format_date   
            cfc_id = context.get('active_id', 0)
            cfc_code = self.pool.get('account.cashflow.code').browse(cr, uid, cfc_id).code
            date_start = format_date(cr, uid, datetime.strptime(context['date_start'], '%Y-%m-%d').date(), context) 
            date_stop = format_date(cr, uid, datetime.strptime(context['date_stop'], '%Y-%m-%d').date(), context) 
            view_header = cfc_code + ': ' + date_start + '..' + date_stop
            return view_header
        return False
    
account_cashflow_line()

class account_cashflow_opening_balance(osv.osv):
    """
    The Opening Balances are stored in a separate table for performance reasons.  
    Use the 'calc.cashflow.opening.balance' wizard for new installs or in case of database corruption.
    """
    _name = 'account.cashflow.opening.balance'
    _description = 'Table to store Cash Flow opening balances'
    _order = 'date desc'
    
    _columns = {
        'date': fields.date('Valuta Date', readonly=True),
        'balance': fields.float('Opening balance', digits_compute=dp.get_precision('Account'), readonly=True),
        'journal_id': fields.many2one('account.journal', 'Financial Journal', required=True, readonly=True), 
        'company_id': fields.related('journal_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
    }

    def calc_opening_balance(self, cr, uid, date, balance_init_id, journal_ids):
        """
        Method to update account.cashflow.opening.balance table 
        Input parameters: 
            - date : valuta date
            - balance_init_id : id of the company's Cash Flow Code for the Initial Balance
            - company_id
        Calculation logic : opening balance = most recent opening balance plus moves prior to 'val_date'
        Returns : opening balance for requested date and journal_ids
        """
        day_before = (datetime.strptime(date, '%Y-%m-%d').date() - timedelta(1)).isoformat()
        # find opening balance prior to 'val_date'
        balances = []
        for journal_id in journal_ids:
            cr.execute("SELECT date, balance, journal_id FROM account_cashflow_opening_balance \
                WHERE date < %s AND journal_id = %s ORDER BY date DESC LIMIT 1", 
                (date, journal_id))
            balance = cr.dictfetchone()
            if balance:
                balances.append(balance)
        if len(balances) != len (journal_ids):
            selected_journal_ids = [x['journal_id'] for x in balances]
            missing_journal_ids = [x for x in journal_ids if x not in selected_journal_ids]
            cr.execute('SELECT s.balance_end_real AS balance, j.id as journal_id, s.date AS date ' \
                        'FROM account_bank_statement s ' \
                        'INNER JOIN account_journal j ON s.journal_id = j.id ' \
                        'INNER JOIN ' \
                            '(SELECT journal_id, max(date) AS max_date FROM account_bank_statement ' \
                                'WHERE date < %s GROUP BY journal_id) d ' \
                                'ON (s.journal_id = d.journal_id AND s.date = d.max_date) ' \
                        'WHERE s.journal_id in %s ' \
                        'ORDER BY j.code', (date, tuple(missing_journal_ids)))
            missing_balances = cr.dictfetchall()
            balances += missing_balances
            if len(balances) != len (journal_ids):
                selected_journal_ids = [x['journal_id'] for x in balances]
                missing_journal_ids = [x for x in journal_ids if x not in selected_journal_ids]
                missing_journals = self.pool.get('account.journal').browse(cr, uid, missing_journal_ids)
                for journal in missing_journals:
                    if journal.default_debit_account_id and (journal.default_credit_account_id == journal.default_debit_account_id):
                        balance = journal.default_debit_account_id.balance
                    else:
                        raise osv.except_osv(_('Error'),_('\nConfiguration Error in journal %s!'    \
                            '\nPlease verify the Default Debit and Credit Account settings.') % journal.name)
                    balances.append({
                        'date': day_before,
                        'balance': balance,
                        'journal_id': journal_id,
                        })

        bal_init_total = 0.0
        for entry in balances:
            date_open = entry['date']
            balance_open = entry['balance']
            journal_id = entry['journal_id']
            # calculate opening balance
            cr.execute('SELECT sum(balance) FROM account_cashflow_balance ' \
                'WHERE date >= %s and date < %s AND journal_id = %s', (date_open, date, journal_id))
            sum_balance = cr.fetchone()
            bal_init = (sum_balance[0] or 0.0) + balance_open
            bal_init_total += bal_init 
            # update or create opening balance
            bal_ids = self.search(cr, uid, [('date', '=', date), ('journal_id', '=', journal_id)])
            if bal_ids:
                self.write(cr, uid, bal_ids, {'balance': bal_init})
            else:
                self.create(cr, uid,
                    {'date': date,
                     'balance': bal_init,
                     'journal_id': journal_id})
        return bal_init_total
    
account_cashflow_opening_balance()

class account_cashflow_balance(osv.osv):
    """
    The Cash Flow Balances are stored in a separate table for performance reasons.  
    Use the 'calc.cashflow.balance' wizard for new installs or in case of database corruption.
    """
    _name = 'account.cashflow.balance'
    _description = 'Table to store daily Cash Flow balances'
    _order = 'date desc'
    
    _columns = {
        'date': fields.date('Valuta Date', readonly=True),
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', domain=[('type', '=', 'normal')], readonly=True),
        'cfc_type': fields.related('cashflow_code_id', 'type', type='char', relation='account.cashflow.code', string='Type', readonly=True),
        'balance': fields.float('Balance', digits_compute=dp.get_precision('Account'), readonly=True,
            help='Cumulative balance of all transactions. The Valuta Date is used to calculate the balance'),
        'journal_id': fields.many2one('account.journal', 'Financial Journal', required=True, readonly=True), 
        'company_id': fields.related('journal_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True)
    }
        
    def update_balance(self, cr, uid, journal_id, values):
        """
        method to update account.cashflow.balance table 
        input : dictionary with keys old_cfc_id, old_val_date, old_amount, new_cfc_id, new_val_date, new_amount
        returns : True
        """
        old_cfc_id = values['old_cfc_id']
        new_cfc_id = values['new_cfc_id']
        old_val_date = values['old_val_date']
        new_val_date = values['new_val_date']
        old_amount = values['old_amount']
        new_amount = values['new_amount']

        # update old
        if old_cfc_id:
            old_ids = self.search(cr, uid, [('cashflow_code_id', '=', old_cfc_id), ('date', '=', old_val_date), ('journal_id', '=', journal_id)])
            if old_ids:
                balance = self.read(cr, uid, old_ids[0], ['balance'])['balance'] 
                self.write(cr, uid, old_ids[0], {'balance': balance - old_amount})
            else:
                cfc_obj = self.pool.get('account.cashflow.code')
                code = cfc_obj.browse(cr, uid, cfc_obj.search(cr, uid, [('id', '=', old_cfc_id)])[0]).code
                raise osv.except_osv('Missing Balance', _("Missing Cash Flow Balance for Cash Flow Code '%s' on Valuta Date '%s'.\nPlease recalculate your Cash Flow Balances !") \
                    % (code, old_val_date))
            
        # update or create new
        if new_cfc_id:
            new_ids = self.search(cr, uid, [('cashflow_code_id', '=', new_cfc_id), ('date', '=', new_val_date), ('journal_id', '=', journal_id)])
            if new_ids:
                balance = self.read(cr, uid, new_ids[0], ['balance'])['balance'] 
                self.write(cr, uid, new_ids[0], {'balance': balance + new_amount})
            else:
                self.create(cr, uid, {
                    'date': new_val_date,
                    'cashflow_code_id': new_cfc_id,
                    'balance': new_amount,
                    'journal_id': journal_id})
        return True

account_cashflow_balance()

class account_cashflow_line_overview(osv.osv):
    _name = 'account.cashflow.line.overview'
    _description = 'Cash Flow Lines Overview'
    _auto = False
    
    _columns = {
        'name': fields.char('Communication', size=64, readonly=True),
        'date': fields.date('Entry Date', readonly=True),
        'val_date': fields.date('Valuta Date', readonly=True),   
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', 
            states={'confirm': [('readonly', True)]}, context={'search_origin': _name}, 
            domain=[('type', '=', 'normal')]),
        'cashflow_type': fields.selection([
            ('normal','Normal'),
            ('provision','Provision'),
            ], 'Cash Flow Type', readonly=True),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), readonly=True),
        'globalisation_id': fields.many2one('account.bank.statement.line.global', 'Globalisation ID', readonly=True),
        'globalisation_amount': fields.related('globalisation_id', 'amount', type='float', 
            relation='account.bank.statement.line.global', string='Glob. Amount', readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal', readonly=True),
        'type': fields.selection([
            ('supplier','Supplier'),
            ('customer','Customer'),
            ('general','General')
            ], 'Type', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'account_id': fields.many2one('account.account','Account', domain=[('type', '!=', 'view')], readonly=True),
        'payment_reference': fields.char('Payment Reference', size=35, readonly=True),
        'note': fields.text('Notes', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'update_date': fields.date('Update Date', readonly=True),
        'update_by': fields.many2one('res.users', 'Updated by', readonly=True),        
        'state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirmed')],
            'State', readonly=True),    
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_cashflow_line_overview')
        cr.execute("""
            CREATE OR REPLACE VIEW account_cashflow_line_overview AS (
            (SELECT
                c.id AS id,
                l.name AS name,                
                l.date AS date,
                l.val_date AS val_date,
                c.cashflow_code_id AS cashflow_code_id,
                'normal' AS cashflow_type,
                l.amount AS amount,
                l.globalisation_id AS globalisation_id,
                l.journal_id AS journal_id,
                l.type AS type,
                l.partner_id AS partner_id,
                l.account_id AS account_id,
                l.payment_reference AS payment_reference, 
                l.note AS note, 
                l.company_id AS company_id, 
                CASE
                    WHEN l.write_date IS NOT NULL THEN date(l.write_date)
                    ELSE date(l.create_date) 
                END AS update_date,
                CASE
                    WHEN l.write_uid IS NOT NULL THEN l.write_uid
                    ELSE l.create_uid 
                END AS update_by,
                l.state AS state
            FROM account_cashflow_line c 
            INNER JOIN account_bank_statement_line l ON (c.st_line_id=l.id) )
            UNION
            (SELECT
                -p.id AS id,
                p.name AS name,                
                p.date AS date,
                p.val_date AS val_date,
                p.cashflow_code_id AS cashflow_code_id,
                'provision' AS cashflow_type,
                p.amount AS amount,
                NULL AS globalisation_id,
                p.journal_id AS journal_id,
                p.type AS type,
                p.partner_id AS partner_id,
                p.account_id AS account_id,
                p.payment_reference AS payment_reference, 
                p.note AS note, 
                p.company_id AS company_id, 
                CASE
                    WHEN p.write_date IS NOT NULL THEN date(p.write_date)
                    ELSE date(p.create_date) 
                END AS update_date,
                CASE
                    WHEN p.write_uid IS NOT NULL THEN p.write_uid
                    ELSE p.create_uid 
                END AS update_by,
                p.state AS state
            FROM account_cashflow_provision_line p )
            );
            
        """)

    def create(self, cr, uid, vals, context=None):
        raise osv.except_osv('Warning', _('No record creation allowed from this screen.'))
        return super(account_cashflow_line_overview, self).create(cr, uid, vals, context=context) 

    def write(self, cr, uid, ids, vals, context={}):
        # limit updates to the casflow_code_id field
        cline_obj = self.pool.get('account.cashflow.line')                
        pline_obj = self.pool.get('account.cashflow.provision.line')
        cfc_obj = self.pool.get('account.cashflow.code')     
        for line in self.browse(cr, uid, ids, context):
            cfc_id = vals.get('cashflow_code_id')
            if cfc_id:
                cfc = cfc_obj.browse(cr, uid, cfc_id, context=context)
                if line.id < 0:
                    upd_obj = pline_obj 
                    upd_ids = [-line.id]
                    cfc_id = cfc.twin_id.id
                else:
                    upd_obj = cline_obj 
                    upd_ids = [line.id]                
                upd_obj.write(cr, uid, upd_ids, {'cashflow_code_id': cfc_id}, context=context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for line_id in ids:
            if line_id > 0:
                return self.pool.get('account.cashflow.line').unlink(cr, uid, [line_id], context=context)
            else:
                return self.pool.get('account.cashflow.provision.line').unlink(cr, uid, [-line_id], context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('active_model', False) == 'account.cashflow.code':
            cfc_obj = self.pool.get('account.cashflow.code')
            cfc_id = context.get('active_id', 0)
            cfc = cfc_obj.browse(cr, uid, cfc_id, context=context)
            def _ids_get(record):
                if record.type in ['normal', 'provision']:
                    ids = [record.id, record.twin_id.id]
                else:
                    ids = []
                if record.type == 'view':
                    for child in record.child_ids:
                        ids += _ids_get(child)
                return ids
            cfc_ids = list(set(_ids_get(cfc)))            
            active_column = context.get('tree_but_open_column')
            if active_column and active_column[:11] == 'balance_day': 
                date_start = date_stop = context.get('active_day')
            else:
                date_start = context.get('date_start', time.strftime('%Y-%m-%d'))
                date_stop = context.get('date_stop', time.strftime('%Y-%m-%d'))
            args += [('cashflow_code_id', 'in', cfc_ids), ('val_date', '>=', date_start), ('val_date', '<=', date_stop)]
        return super(account_cashflow_line_overview, self).search(cr, uid, args, offset, limit, order, context, count)   

account_cashflow_line_overview()
        