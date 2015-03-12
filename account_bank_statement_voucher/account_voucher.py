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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm,fields
from openerp.tools.translate import _
from openerp import netsvc
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)

class account_voucher(orm.Model):
    _inherit = 'account.voucher'

    def _check_paid(self, cr, uid, ids, name, args, context=None):
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            ok = True
            for line in voucher.move_ids:
                #if (line.account_id.type, 'in', ('receivable', 'payable')) and not line.reconcile_id:
                if (line.account_id.type in ('receivable', 'payable')) and not line.reconcile_id: # FIX by Noviat
                    ok = False
            res[voucher.id] = ok
        return res

    def _get_narration(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('act_window_from_bank_statement'):           
            stline = self.pool.get('account.bank.statement.line').browse(cr, uid, context['active_id'], context=context)
            info = _('Partner')  + ': %s' %stline.partner_id.name 
            info += _('\nAmount') + ': %.2f ' %stline.amount + '%s' %(stline.statement_id.journal_id.currency.name or stline.statement_id.journal_id.company_id.currency_id.name)
            if getattr(stline, 'val_date', False):
                val_date = stline.val_date
            else:
                val_date = False
            info += val_date and (_('\nValuta Date') + ': ' + val_date) or (_('\nDate') + ': ' + stline.date)
            info += _('\nCommunication') + ': ' + (stline.name)
            if getattr(stline, 'payment_reference', False):
                info += _('\nPayment Reference') + ': ' + (stline.payment_reference)
            return info
        else:
            return super(account_voucher, self)._get_narration(cr, uid, context=context)

    def _get_stline_info(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        stline_obj = self.pool.get('account.bank.statement.line')
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            info = ''
            stline_id = stline_obj.search(cr, uid, [('voucher_id', '=', voucher.id)])
            if stline_id:
                stline = stline_obj.browse(cr, uid, stline_id[0], context=context)
                info = _('Partner')  + ': %s, ' %stline.partner_id.name 
                info += _('Amount') + ': %.2f ' %stline.amount + '%s, ' %(stline.statement_id.journal_id.currency.name or stline.statement_id.journal_id.company_id.currency_id.name)
                if getattr(stline, 'val_date', False):
                    val_date = stline.val_date
                else:
                    val_date = False
                info += val_date and (_('Valuta Date') + ': ' + val_date) or (_('Date') + ': ' + stline.date)
                info += ', ' + _('Communication') + ': ' + (stline.name)
                if getattr(stline, 'payment_reference', False):
                    info += ', ' + _('\nPayment Reference') + ': ' + stline.payment_reference
            res[voucher.id] =  info
        return res
    
    def _get_invoice(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('invoice_id', False)

    _columns = {
        'paid': fields.function(_check_paid, string='Paid', type='boolean', help="The Voucher has been totally paid."),
        'invoice_id':fields.many2one('account.invoice', 'Invoice', readonly=True, states={'draft':[('readonly',False)]},
            help="Contains link to invoice, e.g. when the voucher is created via the Invoice 'Payment' button."),
        'stline_info': fields.function(_get_stline_info, method=True, string='Associated Bank Transaction', type='char', size=256, readonly=True),
    }
    _defaults = {
        'invoice_id': _get_invoice,
        'narration': _get_narration,
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
    
    def action_move_line_create(self, cr, uid, ids, context=None):
        res = super(account_voucher, self).action_move_line_create(cr, uid, ids, context=context)
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        st_line_obj = self.pool.get('account.bank.statement.line')
        st_obj = self.pool.get('account.bank.statement')
        for voucher in self.browse(cr, uid, ids, context=context):
            move = voucher.move_id
            move_obj.post(cr, uid, [move.id])
            st_line_ids = st_line_obj.search(cr, uid, [('voucher_id', '=', voucher.id)])
            for st_line_id in st_line_ids:
                st_line = st_line_obj.browse(cr, uid, st_line_id)
                st_line_obj.write(cr, uid, [st_line.id], {'move_ids': [(4, move.id)]})
                move_line_obj.write(cr, uid, [x.id for x in move.line_id], {'statement_id': st_line.statement_id.id}, context=context)
        return res

class account_voucher_line(orm.Model):
    """ 
    Remove voucher lines when associated accounting move is deleted (e.g. via cancel invoice).
    """
    _inherit = 'account.voucher.line'
    _columns = {    
        'move_line_id': fields.many2one('account.move.line', 'Journal Item', ondelete='cascade'),
    }

