# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.be). All rights reserved.
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
import logging
_logger = logging.getLogger(__name__)
from tools.translate import _

class account_bank_statement_line(osv.osv):
    _inherit = 'account.bank.statement.line'

    def create(self, cr, uid, vals, context=None):
        #logging.getLogger(self._name).warn('account_cashflow create, vals = %s, context= %s', vals, context)
        if context is None:
            context = {}
        
        st_obj = self.pool.get('account.bank.statement')
        cfline_obj = self.pool.get('account.cashflow.line')
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        journal_obj = self.pool.get('account.journal')
        rule_obj = self.pool.get('account.cashflow.rule')
        cfbalance_obj = self.pool.get('account.cashflow.balance')
        glob_line_obj = self.pool.get('account.bank.statement.line.global')
        currency_obj = self.pool.get('res.currency')

        # The GTK 6.1-1 client doesn't pass the 'statement_id' when hitting a button in a o2m child object.
        # In order to bypass this issue, the end-user needs to save the parent object first (e.g. via the Compute button) 
        if not vals.get('statement_id'):
            raise osv.except_osv(_('Error !'),
                _("Please recalculate the statement balance first via the 'Compute' button"))
            
        journal = st_obj.browse(cr, uid, vals['statement_id'], context=context).journal_id
        journal_id = journal.id
        currency = journal.currency
        company_id = journal.company_id.id
        digits = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        date = vals['date']
        val_date = vals.get('val_date', False)
        if not val_date:
            val_date = date.split()[0]
            vals['val_date'] = val_date
        amount = vals['amount']
        name = vals.get('name', False)
        payment_reference = vals.get('payment_reference', False)
        partner_id = vals.get('partner_id', None)
        account_id = vals.get('account_id', None)
        globalisation_id = vals.get('globalisation_id', None)
        cfline_vals = {}
        cfc_id =  None

        # check provisions
        amount_fmt = '%.' + str(digits) + 'f'
        # search within range of 5 days to cope with delays between expected and actual valuta date
        val_date_limit = (datetime.strptime(val_date, '%Y-%m-%d').date() - timedelta(days=5)).isoformat()
        domain = [('journal_id', '=', journal_id), ('company_id', '=', company_id), 
            ('val_date', '>=', val_date_limit), ('val_date', '<=', val_date)]
        if name:
            domain += ['|', ('name', '=', name), ('name', '=', False)]
        if payment_reference:
            domain += ['|', ('payment_reference', '=', payment_reference), ('payment_reference', '=', False)]
            
        if globalisation_id:  # check matching entry on globalisation level
            glob_line = glob_line_obj.browse(cr, uid, globalisation_id, context=context)
            globalisation_amount = glob_line.amount
            # check globalisation hierarchy for matching record
            def _ids_get(child):
                ids = [child.id]
                if child.parent_id:
                    parent = child.parent_id
                    ids += _ids_get(parent)
                return ids            
            glob_ids = _ids_get(glob_line)
            glob_lines = glob_line_obj.browse(cr, uid, glob_ids, context=context)
            glob_amounts = []
            for l in glob_lines:
                glob_amounts += [ amount_fmt % round(l.amount, digits) ]
            glob_domain = domain + [('amount', 'in', glob_amounts)]
            cfpline_ids = cfpline_obj.search(cr, uid, glob_domain, context=context)
            if len(cfpline_ids) > 1:
                raise osv.except_osv('Warning', _('Cash Flow Provision Line ambiguity, cf. lines %s') % cfpline_ids)
            elif len(cfpline_ids) == 1:
                cfpline = cfpline_obj.browse(cr, uid, cfpline_ids[0], context=context)
                cfc_id = cfpline.cashflow_code_id.twin_id.id
                if cfpline.type:
                    vals['type'] = cfpline.type
                if cfpline.account_id.id:
                    vals['account_id'] = cfpline.account_id.id
                # check partial vs complete reconcile
                total = amount
                for line in cfpline.cfline_partial_ids:
                    total += (line.amount)
                if currency_obj.is_zero(cr, uid, currency, cfpline.amount - total):
                    cfpline_obj.write(cr, uid, [cfpline.id], {'state': 'draft'})            
                    cfpline_obj.unlink(cr, uid, [cfpline.id])
                else:
                    cfline_vals['cfpline_rec_partial_id'] = cfpline.id
           
        if not cfc_id: # check transaction line detail when no matching global entry            
            detail_domain = domain + [('amount', '=', amount_fmt % round(amount, digits))]
            if partner_id:
                detail_domain += ['|', ('partner_id', '=', partner_id), ('partner_id', '=', False)]
            cfpline_ids = cfpline_obj.search(cr, uid, detail_domain, context=context)

            if len(cfpline_ids) > 1:
                _logger.warn('Cash Flow Provision Line ambiguity, cf. lines %s', cfpline_ids) 
                raise osv.except_osv('Warning', _('Cash Flow Provision Line ambiguity, cf. lines %s') % cfpline_ids)
            elif len(cfpline_ids) == 1:
                cfpline = cfpline_obj.browse(cr, uid, cfpline_ids[0], context=context)
                cfc_id = cfpline.cashflow_code_id.twin_id.id
                if cfpline.type:
                    vals['type'] = cfpline.type
                if cfpline.account_id.id:
                    vals['account_id'] = cfpline.account_id.id
                cfpline_obj.write(cr, uid, [cfpline.id], {'state': 'draft'})            
                cfpline_obj.unlink(cr, uid, [cfpline.id])

        # assign code via rules engine if not done via provision line reconciliation
        if not cfc_id:
            kwargs = {'context' :context} 
            kwargs['journal_id'] = journal_id
            kwargs['company_id'] = company_id
            kwargs['account_id'] = account_id
            kwargs['partner_id'] = partner_id
            kwargs['sign'] = amount >= 0 and 'debit' or 'credit'
            if context.get('extra_fields', None):
                kwargs['extra_fields'] = context['extra_fields']
            cfc_id = rule_obj.cfc_id_get(cr, uid, **kwargs)

        # create Bank Statement Line and Cash Flow line
        res_id = super(account_bank_statement_line, self).create(cr, uid, vals, context=context)
        cfline_vals.update({                     
           'cashflow_code_id' : cfc_id,
           'st_line_id' : res_id
        })
        cfline_obj.create(cr, uid, cfline_vals, context=context)

        # update Cash Flow Balances table
        if cfline_vals['cashflow_code_id']:
            values = {
                'old_cfc_id': False,
                'new_cfc_id': cfline_vals['cashflow_code_id'],
                'old_val_date': False,
                'new_val_date': val_date,
                'old_amount': False,
                'new_amount': amount,                    
            }
            cfbalance_obj.update_balance(cr, uid, values)        

        return res_id

    def write(self, cr, uid, ids, vals, context={}):        
        cfline_obj = self.pool.get('account.cashflow.line')
        cfbalance_obj = self.pool.get('account.cashflow.balance')

        for stline in self.browse(cr, uid, ids, context): 
            if vals.has_key('val_date') or vals.has_key('amount'):

                old_val_date = stline.val_date
                old_amount = stline.amount
                
                if vals.has_key('val_date'):
                    val_date = vals['val_date']
                    if not val_date:                 # update empty val_date with value of date field
                        vals['val_date'] = val_date = stline.date
                else:
                    val_date = old_val_date
                    
                if vals.has_key('amount'):
                    amount = vals['amount']
                else:
                    amount = old_amount
                    
                # update Cash Flow Balances table
                cfline_ids = cfline_obj.search(cr, uid, [('st_line_id', '=', stline.id)])
                if cfline_ids:
                    cashflow_code = cfline_obj.browse(cr, uid, cfline_ids[0]).cashflow_code_id
                    if cashflow_code:
                        values = {
                            'old_cfc_id': cashflow_code.id,
                            'new_cfc_id': cashflow_code.id,
                            'old_val_date': old_val_date,
                            'new_val_date': val_date,
                            'old_amount': old_amount,
                            'new_amount': amount,                    
                        }
                        cfbalance_obj.update_balance(cr, uid, values)        

        return super(account_bank_statement_line, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        cfline_obj = self.pool.get('account.cashflow.line')
        cfbalance_obj = self.pool.get('account.cashflow.balance')

        # update Cash Flow Balances table
        for stline in self.browse(cr, uid, ids, context): 
            cfline_ids = cfline_obj.search(cr, uid, [('st_line_id', '=', stline.id)])
            if cfline_ids:
                cfline = cfline_obj.browse(cr, uid, cfline_ids[0])
                if cfline.cashflow_code_id:
                    values = {
                        'old_cfc_id': cfline.cashflow_code_id.id,
                        'new_cfc_id': False,
                        'old_val_date': stline.val_date,
                        'new_val_date': False,
                        'old_amount': stline.amount,
                        'new_amount': False,                    
                    }
                    cfbalance_obj.update_balance(cr, uid, values)        

        return super(account_bank_statement_line, self).unlink(cr, uid, ids, context=context)
       
account_bank_statement_line()

class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'

    def unlink(self, cr, uid, ids, context=None):
        cfline_obj = self.pool.get('account.cashflow.line')
        cfbalance_obj = self.pool.get('account.cashflow.balance')

        # update Cash Flow Balances table
        for st in self.browse(cr, uid, ids, context): 
            for stline in st.line_ids:
                cfline_ids = cfline_obj.search(cr, uid, [('st_line_id', '=', stline.id)])
                if cfline_ids:
                    cfline = cfline_obj.browse(cr, uid, cfline_ids[0])
                    if cfline.cashflow_code_id:
                        values = {
                            'old_cfc_id': cfline.cashflow_code_id.id,
                            'new_cfc_id': False,
                            'old_val_date': stline.val_date,
                            'new_val_date': False,
                            'old_amount': stline.amount,
                            'new_amount': False,                    
                        }
                        cfbalance_obj.update_balance(cr, uid, values)        

        return super(account_bank_statement, self).unlink(cr, uid, ids, context=context)
    
account_bank_statement()

        