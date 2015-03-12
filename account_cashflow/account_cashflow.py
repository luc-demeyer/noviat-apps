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
from datetime import datetime, date, timedelta
import tools
from osv import osv, fields
import decimal_precision as dp
import netsvc
logger=netsvc.Logger()
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
        #logger.notifyChannel('addons.' + self._name, netsvc.LOG_WARNING, '_balance_period, ids = %s' % (ids)) 
        if context is None:
            context = {}
        if not date_start:
            date_start = context.get('date_start', None)
        if not date_stop:
            date_stop = context.get('date_stop', None)
        company_id = context.get('company_id', self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,)

        if day:
            date_start = day        
            cr.execute('SELECT cashflow_code_id, balance FROM account_cashflow_balance WHERE date = %s', (day,))
        elif date_start:
            cr.execute('SELECT cashflow_code_id, sum(balance) FROM account_cashflow_balance ' \
                'WHERE date >= %s AND date <= %s GROUP BY cashflow_code_id',
                (date_start, date_stop))            
        else:
            cr.execute('SELECT id, 0.0 as amount FROM account_cashflow_code ')
        res=dict(cr.fetchall())
       
        # calculate period balance
        balopen_obj = self.pool.get('account.cashflow.opening.balance')
        balance_init_id = context.get('balance_init_id', None)
        if date_start:
            cr.execute("SELECT date FROM account_cashflow_opening_balance \
                WHERE date < %s AND active=TRUE AND company_id = %s ORDER BY date DESC LIMIT 1", 
                (date_start, company_id))
            res_date_open = cr.fetchone()
            date_open = res_date_open[0]
            cr.execute("SELECT balance FROM account_cashflow_opening_balance \
                WHERE date = %s AND active=TRUE AND company_id = %s", 
                (date_open, company_id))
            res_balance_open = cr.fetchone()
            balance_open = res_balance_open[0]
            cr.execute('SELECT sum(balance) FROM account_cashflow_balance ' \
                'WHERE date >= %s and date < %s', (date_open, date_start))
            sum_balance = cr.fetchone()
            res_init = (sum_balance[0] or 0.0) + balance_open           
            # recalculate opening balance for each day in order to support chart 'reload' actions after move update
            if day:
                balopen_obj.calc_opening_balance(cr, uid, date_start, balance_init_id, company_id)
            balance_init = {balance_init_id: res_init}
        else:
            balance_init = {balance_init_id: 0.0}            
        res.update(balance_init)    

        dp = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')        
        res2 = {}
        def _rec_get(record):
            amount = res.get(record.id, 0.0)
            for rec in record.child_ids:
                amount += _rec_get(rec) * rec.parent_sign
            return amount
        for record in self.browse(cr, uid, ids, context=context):
            res2[record.id] = round(_rec_get(record), dp)
        return res2

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
        if context.has_key('nbr_days'):
            nbr_days = int(context.get('nbr_days'))            
            for x in range(nbr_days+1,43):
                if x < 10:
                    field = 'balance_day0' + str(x)
                else:
                    field = 'balance_day' + str(x)
#                res['arch'] = res['arch'].replace('name="' + field + '"', 'name="' + field + '" invisible="1"')
                res['arch'] = res['arch'].replace('<field name="' + field + '"', '')        
        return res

    _columns = {
        'name': fields.char('Description', size=128, required=True, translate=True),
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

    def onchange_parent_id(self, cr, uid, ids, parent_id, context=None):
        parent = self.browse(cr, uid, parent_id, context=context)
        return {'value': {'sequence': parent.sequence}}

    def copy(self, cr, uid, id, default=None, context=None):
        cfc = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default.update({'st_line_ids': []})
        default['code'] = cfc.code + ' (copy)'
        return super(account_cashflow_code, self).copy(cr, uid, id, default, context) 
    
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
        #logger.notifyChannel('addons.' + self._name, netsvc.LOG_WARNING, 'search, args = %s' % (args)) 
        if context is None:
            context = {}
        elif context.get('search_origin') == 'account.cashflow.line.overview':
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

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        res_id = super(account_cashflow_code, self).create(cr, uid, vals, context=context)
        cfc_type = vals.get('type')
        if cfc_type in ['normal', 'provision'] and not context.get('create_cfc_twin'):
            twin_vals = vals.copy()
            twin_vals['type'] = cfc_type == 'normal' and 'provision' or 'normal'
            twin_vals['twin_id'] = res_id
            twin_id = self.create(cr, uid, twin_vals, context={'create_cfc_twin': 1})
            if not twin_id:
                raise osv.except_osv('Error', _("Configuration Error !"))
            self.write(cr, uid, [res_id], {'twin_id': twin_id}, context={'create_cfc_twin': 1})
        return res_id

    def write(self, cr, uid, ids, vals, context={}):
        unlink_ids = []
        if not context.get('create_cfc_twin') and not context.get('update_cfc_twin'):
            for cfc in self.browse(cr, uid, ids, context=context):
                if cfc.type in ['normal', 'provision']:
                    twin_vals = vals.copy()
                    if twin_vals.get('type'):
                        twin_vals['type'] = cfc.type == 'normal' and 'provision' or 'normal'
                    self.write(cr, uid, [cfc.twin_id.id], twin_vals, context={'update_cfc_twin': 1})
                else:
                    twin_id = cfc.twin_id
                    if twin_id:
                        vals['twin_id'] = None
                        unlink_ids.append(twin_id.id)
        res = super(account_cashflow_code, self).write(cr, uid, ids, vals, context)
        self.unlink(cr, uid, unlink_ids)
        return res
    

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
            ('debit', 'Debit'),
            ('credit', 'Credit'),
            ], 'Movement Sign',
            help='Sign for the Cash Flow Code Assignment'),
        'journal_id': fields.many2one('account.journal', 'Journal', ondelete='cascade', domain=[('type', 'in', ['bank', 'cash'])]),
        'account_id': fields.many2one('account.account', 'Account', ondelete='cascade', domain=[('type', '!=', 'view')]),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'active': fields.boolean('Active', help='Switch off this rule.'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'active': True,                 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    def cfc_id_get(self, cr, uid, sign=None, account_id=None, journal_id=None, partner_id=None, 
                   extra_fields={}, company_id=None, context=None):       
        ''' 
        The extra_fields dictionary (extra_fields = {fieldname1: value1, field_name2: value2, ... )) 
        allows addition of customer specific criteria via inheritance:
        - add extra fields (fieldname1, fieldname2, ... ) to account.cashflow.rule;
        - add extra_fields to the context ('extra_fields': [ (fieldname1, value1, operand1), (fieldname2, value2, operand2), ... ] ) of the create() method of account.bank.statement.line.
        '''

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
        'update_date': fields.date('Update Date', required=True, readonly=True),
        'update_by': fields.many2one('res.users', 'Updated by', required=True, readonly=True),        
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
        'update_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'update_by': lambda s, c, u, ctx: u,
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
                    cfbalance_obj.update_balance(cr, uid, values)
        vals['update_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        vals['update_by'] = uid
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
            cfbalance_obj.update_balance(cr, uid, values)
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
            cfbalance_obj.update_balance(cr, uid, values)   
        return super(account_cashflow_provision_line, self).unlink(cr, uid, ids, context=context)
         
account_cashflow_provision_line()

class account_cashflow_line(osv.osv):
    _name = 'account.cashflow.line'
    _description = 'Cash Flow Line'
    _inherits = {'account.bank.statement.line': 'st_line_id'}
    _columns = {
        'st_line_id': fields.many2one('account.bank.statement.line', 'Bank Statement Line', ondelete='cascade', 
            required=True, states={'confirm': [('readonly', True)]}),
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', 
            domain=[('type', '=', 'normal')], states={'confirm': [('readonly', True)]}),
        'cfpline_rec_partial_id': fields.many2one('account.cashflow.provision.line', 'Partially Reconciled Provision Line', readonly=True, ondelete='set null'),
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
                    cfbalance_obj.update_balance(cr, uid, values)
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
    _name = 'account.cashflow.opening.balance'
    _description = 'Table to store Cash Flow opening balances'
    _order = 'date desc'
    
    _columns = {
        'date': fields.date('Valuta Date', required=True, states={'confirm': [('readonly', True)]}),
        'balance': fields.float('Opening balance', digits_compute=dp.get_precision('Account'), required=True, states={'confirm': [('readonly', True)]}),
        'active': fields.boolean('Active', required=True, states={'confirm': [('readonly', True)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True, states={'confirm': [('readonly', True)]}),   
        'state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirmed')],
            'State', required=True, readonly=True),    
    }
    _defaults = {
        'active': True,
        'state': 'draft',
        'balance': 0.0,         
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    def unlink(self, cr, uid, ids, context=None):        
        for balance in self.read(cr, uid, ids, ['state'], context=context):
            if balance['state'] == 'confirm':
                raise osv.except_osv('Warning', _('Delete operation not allowed !'))
        return super(account_cashflow_opening_balance, self).unlink(cr, uid, ids, context=context)
    
    def action_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'confirm'})
        return True

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True

    def calc_opening_balance(self, cr, uid, date, balance_init_id, company_id):
        """
        Method to update account.cashflow.opening.balance table 
        Input parameters: 
            - date : valuta date
            - balance_init_id : id of the company's Cash Flow Code for the Initial Balance
            - company_id
        Calculation logic : opening balance = most recent opening balance plus moves prior to 'val_date'
        Returns : True
        """
        # find opening balance prior to 'val_date'
        cr.execute("SELECT date, balance FROM account_cashflow_opening_balance \
            WHERE date < %s AND active=TRUE AND company_id = %s ORDER BY date DESC LIMIT 1", 
            (date, company_id))
        res_open = cr.fetchone()
        if not res_open:
            raise osv.except_osv('Configuration Error', _("Please check if you have an active Opening Balance prior to the selected period !"))         
        date_open = res_open[0]
        balance_open = res_open[1]
        # calculate opening balance
        cr.execute('SELECT sum(balance) FROM account_cashflow_balance ' \
            'WHERE date >= %s and date < %s AND company_id = %s', (date_open, date, company_id))
        sum_balance = cr.fetchone()
        res_init = (sum_balance[0] or 0.0) + balance_open
        # update or create opening balance
        bal_ids = self.search(cr, uid, [('date', '=', date)])
        if bal_ids:
            self.write(cr, uid, bal_ids,
                {'date': date,
                 'balance': res_init,
                 'active': True,
                 'state': 'confirm'})
        else:
            self.create(cr, uid,
                {'date': date,
                 'balance': res_init,
                 'active': True,
                 'state': 'confirm'})       
        return True
    
account_cashflow_opening_balance()

class account_cashflow_balance(osv.osv):
    _name = 'account.cashflow.balance'
    _description = 'Table to store daily Cash Flow balances'
    _order = 'date desc'
    
    _columns = {
        'date': fields.date('Valuta Date', required=True, states={'confirm': [('readonly', True)]}),
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', domain=[('type', '=', 'normal')], required=True, states={'confirm': [('readonly', True)]}),
        'cfc_type': fields.related('cashflow_code_id', 'type', type='char', relation='account.cashflow.code', string='Type', readonly=True),
        'balance': fields.float('Balance', digits_compute=dp.get_precision('Account'), required=True, states={'confirm': [('readonly', True)]},
            help='Cumulative balance of all transactions till the entry date. The Valuta Date is used to calculate the balance'),
        'company_id': fields.many2one('res.company', 'Company', required=True, states={'confirm': [('readonly', True)]}),   
        'state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirmed')],
            'State', required=True, readonly=True),    
    }
    _defaults = {
        'balance': 0.0,         
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'state': 'draft',
    }

    def unlink(self, cr, uid, ids, context=None):        
        for balance in self.read(cr, uid, ids, ['state'], context=context):
            if balance['state'] == 'confirm':
                raise osv.except_osv('Warning', _('Delete operation not allowed !'))
        return super(account_cashflow_balance, self).unlink(cr, uid, ids, context=context)
    
    def action_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'confirm'})
        return True

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    def update_balance(self, cr, uid, values={}):
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
            old_ids = self.search(cr, uid, [('cashflow_code_id', '=', old_cfc_id), ('date', '=', old_val_date)])
            if old_ids:
                balance = self.read(cr, uid, old_ids[0], ['balance'])['balance'] 
                self.write(cr, uid, old_ids[0], {'balance': balance - old_amount, 'state': 'confirm'})
            else:
                cfc_obj = self.pool.get('account.cashflow.code')
                code = cfc_obj.browse(cr, uid, cfc_obj.search(cr, uid, [('id', '=', old_cfc_id)])[0]).code
                raise osv.except_osv('Missing Balance', _("Please recalculate your Cash Flow Balances or enter your Cash Flow Balance for Cash Flow Code '%s' on Valuta Date '%s' !") \
                    % (code, old_val_date))
            
        # update or create new
        if new_cfc_id:
            new_ids = self.search(cr, uid, [('cashflow_code_id', '=', new_cfc_id), ('date', '=', new_val_date)])
            if new_ids:
                balance = self.read(cr, uid, new_ids[0], ['balance'])['balance'] 
                self.write(cr, uid, new_ids[0], {'balance': balance + new_amount})
            else:
                self.create(cr, uid, {
                    'date': new_val_date,
                    'cashflow_code_id': new_cfc_id,
                    'balance': new_amount,
                    'state': 'confirm',
                    })
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
                l.update_date AS update_date,
                l.update_by AS update_by, 
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
                p.update_date AS update_date,
                p.update_by AS update_by, 
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
        