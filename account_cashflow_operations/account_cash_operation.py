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
from osv import osv, fields
import decimal_precision as dp
import netsvc
from tools.translate import _
logger=netsvc.Logger()

def _lang_get(self, cr, uid, context={}):
    obj = self.pool.get('res.lang')
    ids = obj.search(cr, uid, [], context=context)
    res = obj.read(cr, uid, ids, ['code', 'name'], context)
    return [(r['code'], r['name']) for r in res] + [('','')]

class account_cash_operation(osv.osv):
    _name= 'account.cash.operation'
    _description= 'Object to store Cash Operation Demands'
    _order = 'date desc'

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('type', 'loan')

    def _amount_interest(self, cr, uid, ids, field_name, arg, context):
        result = {}
        for demand in self.browse(cr, uid, ids, context=context):
            result[demand.id] = demand.amount_main * (demand.rate/100) * (demand.days/float(demand.day_count_basis))
        return result

    def _amount_end(self, cr, uid, ids, field_name, arg, context):
        result = {}
        for demand in self.browse(cr, uid, ids, context=context):
            if demand.interest_payment == 'pre':
                result[demand.id] = demand.amount_main
            elif demand.interest_payment == 'post':
                result[demand.id] = demand.amount_main + demand.amount_interest
        return result

    _columns = {
        # general fields
        'description': fields.char('Description', size=32, states={'confirm': [('readonly', True)]}),
        'name': fields.char('Reference', size=64, states={'confirm': [('readonly', True)]}),
        'type':fields.selection([
            ('loan','Loan'),
            ('invest','Investment'),
        ],'Type', help="Type is used to separate Loans and Investments."),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed')],            
            'State', required=True, readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        # loan/invest demand fields
        'date_start': fields.date('Start Date', states={'confirm': [('readonly', True)]}),
        'date_stop': fields.date('Maturity Date', states={'confirm': [('readonly', True)]}),
        'days': fields.integer('Interest Days', required=True, states={'confirm': [('readonly', True)]}),
        'rate': fields.float('Interest Rate (%)', required=True, states={'confirm': [('readonly', True)]}),
        'interest_payment': fields.selection([
            ('pre', 'In Advance'),
            ('post', 'On Maturity Date')],            
            'Interest Payment', required=True, states={'confirm': [('readonly', True)]}),
        'day_count_basis': fields.selection([
            ('360', '360'),
            ('365', '365')],            
            'Day Count Basis', required=True, states={'confirm': [('readonly', True)]}),
        'amount_main': fields.float('Transaction Amount', digits_compute=dp.get_precision('Account'), required=True, states={'confirm': [('readonly', True)]}),
        'amount_cost': fields.float('Transaction Costs', digits_compute=dp.get_precision('Account'), required=True, states={'confirm': [('readonly', True)]}),
        'bank_id': fields.many2one('res.partner.bank', 'Bank Account', required=True, states={'confirm': [('readonly', True)]},
            change_default=True, help='Bank Account Number.'),
        # confirmation letter fields
        'partner_id': fields.many2one('res.partner', 'Partner', change_default=True, required=True, states={'confirm':[('readonly', True)]}),
        'partner_address_id': fields.many2one('res.partner.address', 'Contact Address', required=True, states={'confirm':[('readonly', True)]}),
        'partner_contact': fields.char('Contact Name', size=64, required=True, states={'confirm': [('readonly', True)]}),
        'partner_lang': fields.selection(_lang_get, 'Language', required=True, size=5, states={'confirm': [('readonly', True)]},
            help="Documents will be printed in this language."),                                         
        'subject': fields.char('Subject', size=128, required=True, states={'confirm': [('readonly', True)]}),        
        'intro': fields.text('Intro', required=True, states={'confirm': [('readonly', True)]}), 
        'close': fields.text('Close', required=True, states={'confirm': [('readonly', True)]}),
        # cashflow management fields
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, 
            domain=[('type', '=', 'bank')], states={'confirm': [('readonly', True)]}),
        'cfc_id_main_start': fields.many2one('account.cashflow.code', 'Principal Amount Cash Flow Code - Start', required=True, 
            domain=[('type', '=', 'provision')], states={'confirm': [('readonly', True)]},
            help='Cash Flow Code for the Principal Amount at the Start Date'),
        'cfc_id_main_stop': fields.many2one('account.cashflow.code', 'Principal Amount Cash Flow Code - End', required=True, 
            domain=[('type', '=', 'provision')], states={'confirm': [('readonly', True)]},
            help='Cash Flow Code for the Principal Amount at the Maturity Date'),                 
        'cfc_id_interest': fields.many2one('account.cashflow.code', 'Interest Cash Flow Code', required=True, 
            domain=[('type', '=', 'provision')], states={'confirm': [('readonly', True)]},
            help='Cash Flow Code for the Interest'),            
        'cfc_id_cost': fields.many2one('account.cashflow.code', 'Transaction Cost Cash Flow Code', required=True, 
            domain=[('type', '=', 'provision')], states={'confirm': [('readonly', True)]},
            help='Cash Flow Code for the Transaction Cost'),            
        'amount_interest': fields.function(_amount_interest, method=True, string='Interest Amount'),
        'amount_end': fields.function(_amount_end, method=True, string='Maturity Date Amount'),
        # traceability fields
        'date': fields.date('Entry Date', required=True, readonly=True),
        'user_id': fields.many2one('res.users','User', readonly=True),
        'update_date': fields.date('Update Date',readonly=True),
        'update_by': fields.many2one('res.users', 'Updated by', readonly=True),        
    }
    _defaults = {
        'type': _get_type,
        'state': 'draft',
        'day_count_basis': '360',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'user_id': lambda self,cr,uid,context: uid,
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.coda', context=c),
    }        

    def onchange_date(self, cr, uid, ids, date_start, date_stop):
        if not (date_start and date_stop):
            return {}
        res = {}
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        date_stop = datetime.strptime(date_stop, '%Y-%m-%d').date()
        nbr_days = (date_stop - date_start).days
        if nbr_days < 1 :
            raise osv.except_osv(_('Error!'), _('Invalid Date Range!'))
            return {}
        return {'value':{'days': nbr_days}}

    def button_confirm(self, cr, uid, ids, context=None):   
        if context is None:
            context = {}
        seq_obj = self.pool.get('ir.sequence')
        seq_sl_code = 'account.straight.loan.demand'
        seq_pl_code = 'account.placement.demand'
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        for demand in self.browse(cr, uid, ids, context=context):
            # amount_main provision
            cfpline_obj.create(cr, uid, {
                'origin': demand._name + ',' + str(demand.id),
                'description': (demand.description and (demand.description + ' - ') or '') + _('Transaction Amount'),
                'state': 'confirm',
                'journal_id': demand.journal_id.id,
                'val_date': demand.date_start,  
                'amount': demand.type == 'loan' and demand.amount_main or -demand.amount_main,
                'cashflow_code_id': demand.cfc_id_main_start.id,
                }, context=context)
            cfpline_obj.create(cr, uid, {
                'origin': demand._name + ',' + str(demand.id),
                'description': (demand.description and (demand.description + ' - ') or '') + _('Transaction Amount'),
                'state': 'confirm',
                'journal_id': demand.journal_id.id,
                'val_date': demand.date_stop,  
                'amount': demand.type == 'loan' and -demand.amount_main or demand.amount_main,
                'cashflow_code_id': demand.cfc_id_main_stop.id,
                }, context=context)
            # amount_cost provision
            if demand.amount_cost:
                cfpline_obj.create(cr, uid, {
                    'origin': demand._name + ',' + str(demand.id),
                    'description': (demand.description and (demand.description + ' - ') or '') + _('Transaction Costs'),
                    'state': 'confirm',
                    'journal_id': demand.journal_id.id,
                    'val_date': demand.date_start,  
                    'amount': -demand.amount_cost,
                    'cashflow_code_id': demand.cfc_id_cost.id,
                    }, context=context)
            # amount_interest provision
            if demand.amount_interest:
                cfpline_obj.create(cr, uid, {
                    'origin': demand._name + ',' + str(demand.id),
                    'description': (demand.description and (demand.description + ' - ') or '') + _('Interest Amount'),
                    'state': 'confirm',
                    'journal_id': demand.journal_id.id,
                    'val_date': demand.interest_payment == 'pre' and demand.date_start or demand.date_stop,  
                    'amount': demand.type == 'loan' and -demand.amount_interest or demand.amount_interest,
                    'cashflow_code_id': demand.cfc_id_interest.id,
                    }, context=context)
            # confirm
            vals = {}
            if not demand.name:
                if demand.type == 'loan':
                    name = seq_obj.get(cr, uid, seq_sl_code)
                else:
                    name = seq_obj.get(cr, uid, seq_pl_code)
                if not name:
                    raise osv.except_osv(_('Error'), _("No Sequence with Code '%s' defined !") %(seq_code))
                vals['name'] = name
            vals['state'] = 'confirm'
            self.write(cr, uid, demand.id, vals, context=context)
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        attachment_obj = self.pool.get('ir.attachment')
        for demand in self.browse(cr, uid, ids, context=context):
        # delete provisions
            cr.execute('SELECT id FROM account_cashflow_provision_line WHERE origin=%s',
                (demand._name + ',' + str(demand.id),))            
            res=cr.fetchall()
            cfpline_ids = [x[0] for x in res]
            cfpline_obj.write(cr, uid, cfpline_ids, {'state': 'draft'})            
            cfpline_obj.unlink(cr, uid, cfpline_ids)
            # delete attached confirmation letters
            cr.execute('SELECT id FROM ir_attachment WHERE res_model=%s and res_id=%s and res_name=%s',
                (demand._name, demand.id, demand.name))
            res = cr.fetchone()
            if res:
                attachment_obj.unlink(cr, uid, [res[0]])
            # set to draft
            vals = {}
            vals['state'] = 'draft'
            self.write(cr, uid, demand.id, vals, context=context)        
        return True
    
    def button_dummy(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {}, context=context)

    def write(self, cr, uid, ids, vals, context={}):
        vals['update_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        vals['update_by'] = uid
        return super(account_cash_operation, self).write(cr, uid, ids, vals, context) 

    def unlink(self, cr, uid, ids, context=None):
        state = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in state:
            if s['state'] in ('draft'):
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _("Only Demands in state 'draft' can be deleted !"))
        return super(account_cash_operation, self).unlink(cr, uid, unlink_ids, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default = default.copy()
        default.update({
        'name': None,
        'state': 'draft',
        'amount_main': None,
        'amount_cost': None,
        'rate': None,
        'amount_interest': None,
        'date_start': None,
        'date_stop': None,
        'days': None,    
        'date': time.strftime('%Y-%m-%d'),
        'user_id': uid,
        })
        return super(account_cash_operation, self).copy(cr, uid, id, default, context)

account_cash_operation()

    
