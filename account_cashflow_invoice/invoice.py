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

from osv import osv, fields
import re
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    _columns = {
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', domain=[('type', '=', 'provision')],
            readonly=True, states={'draft':[('readonly',False)]},
            help="Specify Cash Flow Code in order to override the Cash Flow Code Assignment Rules."),
        'cashflow_journal_id': fields.many2one('account.journal', 'Payment Method', 
            context={'journal_type': False}, domain=[('type', 'in', ['bank','cash'])],            
            readonly=True, states={'draft':[('readonly',False)]},
            help="Specify the financial journal for the payment of this invoice or credit note."),
    }    

    def action_cfc_create(self, cr, uid, ids, *args):
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        for inv in self.browse(cr, uid, ids):
            if inv.type in ['out_invoice', 'in_refund']:
                if inv.currency_id != inv.company_id.currency_id:    # To DO : adapt for multi-currency support
                    continue
                cfpline_amount = inv.amount_total
                cfpline_journal_id = inv.cashflow_journal_id and inv.cashflow_journal_id.id
                cfpline_company_id = inv.journal_id.company_id.id
                cfpline_partner_id = inv.partner_id.id
                cfpline_note = _('Provision for') + ' ' + (inv.type == 'out_invoice' and _('Customer Invoice') or _('Supplier Refund')) + ' ' + inv.internal_number
                cfpline_account_id = inv.account_id.id
                cfpline_type = 'customer'
                cfpline_date = inv.date_due or inv.date_invoice    
                communication =  inv.reference or ''
                cfpline_cfc_id = False
                if inv.cashflow_code_id:
                    cfpline_cfc_id = inv.cashflow_code_id.id
                else:
                    # assign Cash Flow Code via rules engine
                    kwargs = {
                        'journal_id': cfpline_journal_id,
                        'company_id': cfpline_company_id,
                        'account_id': cfpline_account_id,
                        'partner_id': cfpline_partner_id,
                        'sign': cfpline_amount >= 0 and 'debit' or 'credit',
                    }
                    #if context.get('extra_fields', None):
                    #    kwargs['extra_fields'] = context['extra_fields']
                    cfc_id = self.pool.get('account.cashflow.rule').cfc_id_get(cr, uid, **kwargs)
                    if cfc_id:
                        cfpline_cfc_id = self.pool.get('account.cashflow.code').browse(cr, uid, cfc_id).twin_id.id
                if not cfpline_cfc_id:
                    continue
                
                cfpline_obj.create(cr, uid, {
                    'description': (inv.type == 'out_invoice' and _('Customer Invoice') or _('Customer Refund')) + ' ' + inv.internal_number,
                    'cashflow_code_id': cfpline_cfc_id,
                    'state': 'confirm',
                    'note': cfpline_note,
                    'origin': inv._name + ',' + str(inv.id),
                    'journal_id': cfpline_journal_id,
                    'val_date': cfpline_date,  
                    'amount': cfpline_amount,
                    'partner_id': cfpline_partner_id,
                    'name': communication,
                    'company_id': cfpline_company_id,
                    'type': cfpline_type,
                    'account_id': cfpline_account_id,              
                    })

        return True

    def action_cancel(self, cr, uid, ids, *args):
        super(account_invoice, self).action_cancel(cr, uid, ids, *args)
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        for inv in self.browse(cr, uid, ids):
            domain = [ ('origin', '=', inv._name + ',' + str(inv.id))]
            cfpline_ids = cfpline_obj.search(cr, uid, domain)
            if len(cfpline_ids) > 1:
                raise osv.except_osv(_('Warning'), _('Cash Flow Provision Line ambiguity, cf. lines %s') % cfpline_ids)
            elif len(cfpline_ids) == 1:
                cfpline_obj.write(cr, uid, [cfpline_ids[0]], {'state': 'draft'})            
                cfpline_obj.unlink(cr, uid, [cfpline_ids[0]])        
        return True

account_invoice()