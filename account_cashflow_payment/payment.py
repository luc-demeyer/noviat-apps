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

from osv import osv, fields
import re
import netsvc
from tools.translate import _
logger = netsvc.Logger()

class payment_line(osv.osv):
    _inherit = 'payment.line'
    _columns = {
        'cashflow_code_id': fields.many2one('account.cashflow.code', 'Cash Flow Code', domain=[('type', '=', 'provision')],
            help="Specify Cash Flow Code in order to override the Cash Flow Code Assignment Rules.") 
    }    
payment_line()

class payment_order(osv.osv):
    _inherit = 'payment.order'

    def set_done(self, cr, uid, ids, *args):
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        for order in self.browse(cr, uid, ids):
            for line in order.line_ids:
                if line.currency <> line.company_currency: # To DO : adapt for multi-currency support
                    continue
                cfpline_amount = -line.amount_currency

                cfpline_journal_id = order.mode.journal.id
                cfpline_company_id = order.mode.journal.company_id.id
                cfpline_partner_id = line.partner_id.id
                
                if line.ml_inv_ref and line.ml_inv_ref.type in ['in_invoice', 'out_refund']:
                    cfpline_note = line.ml_inv_ref and (_('Payment of Invoice') + ' ' + line.ml_inv_ref.internal_number)
                    if line.ml_inv_ref.type == 'in_invoice':
                        cfpline_account_id = line.partner_id.property_account_payable.id or None
                        cfpline_type = 'supplier'                        
                    else:
                        cfpline_account_id = line.partner_id.property_account_receivable.id or None
                        cfpline_type = 'customer'
                else:
                    cfpline_note = ''
                    cfpline_account_id = None
                    cfpline_type = ''
                
                if line.communication:
                    if line.communication2: 
                        communication = line.communication + ' ' + line.communication2
                    else:
                        communication = line.communication
                else:
                    communication = ''

                if line.cashflow_code_id:
                    cfpline_cfc_id = line.cashflow_code_id.id
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
                    cfpline_cfc_id = self.pool.get('account.cashflow.code').browse(cr, uid, cfc_id).twin_id.id
                if not cfpline_cfc_id:
                    continue
                    
                cfpline_obj.create(cr, uid, {
                    'description': _('Payment Order') + ' ' + order.reference,
                    'cashflow_code_id': cfpline_cfc_id,
                    'state': 'confirm',
                    'note': cfpline_note,
                    'origin': line._name + ',' + str(line.id),
                    'journal_id': cfpline_journal_id,
                    'val_date': line.date,  
                    'amount': cfpline_amount,
                    'partner_id': cfpline_partner_id,
                    'name': communication,
                    'payment_reference': line.name,
                    'company_id': cfpline_company_id,
                    'type': cfpline_type,
                    'account_id': cfpline_account_id,              
                    })

        return super(payment_order, self).set_done(cr, uid, ids, *args)

    def button_undo_payment(self, cr, uid, ids, context=None):
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        for order in self.browse(cr, uid, ids):
            for line in order.line_ids:
                domain = [ ('origin', '=', line._name + ',' + str(line.id))]
                cfpline_ids = cfpline_obj.search(cr, uid, domain)
                if len(cfpline_ids) > 1:
                    raise osv.except_osv(_('Warning'), _('Cash Flow Provision Line ambiguity, cf. lines %s') % cfpline_ids)
                elif len(cfpline_ids) == 1:
                    cfpline_obj.write(cr, uid, [cfpline_ids[0]], {'state': 'draft'})            
                    cfpline_obj.unlink(cr, uid, [cfpline_ids[0]])        
        return super(payment_order, self).button_undo_payment(cr, uid, ids, context)

payment_order()
