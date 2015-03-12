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

from osv import fields, osv
from tools.translate import _
from operator import itemgetter
import netsvc
import logging

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def _stline_info(self, cr, uid, context=None):
        if not context: context={}
        info = ''
        if context.get('act_window_from_bank_statement'):           
            stline = self.pool.get('account.bank.statement.line').browse(cr, uid, context['active_id'], context=context)
            info = _('Partner')  + ': %s' %stline.partner_id.name 
            info += 10*' ' + _('Amount') + ': %.2f ' %stline.amount + '%s' %stline.statement_id.journal_id.currency.name
            info += _('\nDate') + ': ' + (stline.val_date or stline.date)
            info += _('\nCommunication') + ': ' + (stline.name)
            if stline.payment_reference:
                info += _('\nPayment Reference') + ': ' + (stline.payment_reference)
        return info

    def _get_stline_info(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        stline_obj = self.pool.get('account.bank.statement.line')
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            info = ''
            stline_id = stline_obj.search(cr, uid, [('voucher_id', '=', voucher.id)])
            if stline_id:
                stline = stline_obj.browse(cr, uid, stline_id[0], context=context)
                info = _('Partner')  + ': %s' %stline.partner_id.name 
                info += 10*' ' + _('Amount') + ': %.2f ' %stline.amount + '%s' %(stline.statement_id.journal_id.currency.name or stline.statement_id.journal_id.company_id.currency_id.name)
                info += _('\nDate') + ': ' + (stline.val_date or stline.date)
                info += _('\nCommunication') + ': ' + (stline.name)
                if stline.payment_reference:
                    info += _('\nPayment Reference') + ': ' + (stline.payment_reference)
            res[voucher.id] =  info
        return res
    
    def _get_invoice(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('invoice_id', False)
    
    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        return super(account_voucher, self)._get_writeoff_amount(cr, uid, ids, name, args, context=context)
   
    def _compute_writeoff_amount(self, cr, uid, line_dr_ids, line_cr_ids, amount):
        #logging.getLogger(self._name).warn('_compute_writeoff_amount, line_dr_ids=%s, line_cr_ids=%s, amount=%s', line_dr_ids, line_cr_ids, amount)
        debit = credit = 0.0
        for l in line_dr_ids:
            debit += l and l['amount'] or 0.0 # fix by Noviat to support delete of voucher line
        for l in line_cr_ids:
            credit += l and l['amount'] or 0.0 # fix by Noviat to support delete of voucher line
        return abs(amount - abs(credit - debit))

    _columns = {
        'invoice_id':fields.many2one('account.invoice', 'Invoice', readonly=True, states={'draft':[('readonly',False)]},
            help="Contains link to invoice, e.g. when the voucher is created via the Invoice 'Payment' button."),
        'writeoff_amount': fields.function(_get_writeoff_amount, method=True, string='Write-Off Amount', type='float', readonly=True,
            help="The Write-Off Amount is calculated as the difference between the Paid Amount and the sum of the debit/credit lines."),
        'stline_info': fields.function(_get_stline_info, method=True, string='Associated Bank Transaction', type='text', readonly=True),
    }
    _defaults = {
        'invoice_id': _get_invoice,
        'narration': _stline_info,
    }
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        return [(r['id'], (str("%.2f - %s") % (r['amount'], r['state'] == 'proforma' and 'PF' or r['state'][0].upper()) or '')) \
            for r in self.read(cr, uid, ids, ['amount', 'state'], context, load='_classic_write')]

    def button_dummy(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {}, context=context)

    def button_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {}, context=context)
        return {'type': 'ir.actions.act_window_close'}
          
    def cancel_voucher(self, cr, uid, ids, context=None):
        """  
        The standard account_voucher cancel_voucher method does not re-open the associated invoice.
        Fixed via 
           1) lookup invoice_id 
           2) super cancel_voucher
           3) re-open invoice via workflow 
        """
        #logging.getLogger(self._name).warn('cancel_voucher, ids=%s, context=%s', ids, context)
        move_line_obj = self.pool.get('account.move.line')
        inv_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService('workflow')
        inv_ids = []
        for voucher in self.browse(cr, uid, ids, context=context):
            reconcile_ids = []
            move_ids = []
            for move_line in voucher.move_ids:
                if move_line.reconcile_id or move_line.reconcile_partial_id:
                    reconcile_ids.append(move_line.reconcile_id.id or move_line.reconcile_partial_id.id)
            if reconcile_ids:
                move_line_ids = move_line_obj.search(cr, uid, ['|',
                    ('reconcile_id', 'in', reconcile_ids),
                    ('reconcile_partial_id', 'in', reconcile_ids)
                    ])
                for id in move_line_ids: 
                    move_ids.append(move_line_obj.browse(cr, uid, id).move_id.id)
                inv_ids = inv_obj.search(cr, uid, [('move_id', 'in', move_ids)])
        super(account_voucher, self).cancel_voucher(cr, uid, ids, context=context)
        for inv_id in inv_ids:
            result = wf_service.trg_validate(uid, 'account.invoice', inv_id, 'open_test', cr) 
        return True              

account_voucher()

class account_voucher_line(osv.osv):
    """ 
    Remove voucher lines when associated accounting move is deleted (e.g. via cancel invoice).
    """
    _inherit = 'account.voucher.line'
    _columns = {    
        'move_line_id': fields.many2one('account.move.line', 'Journal Item', ondelete='cascade'),
    }
account_voucher_line()
