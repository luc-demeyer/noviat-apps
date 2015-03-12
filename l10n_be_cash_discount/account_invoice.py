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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import translate, _ 
import decimal_precision as dp
import time
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

BaseTaxCodesIn = ['81', '82', '83', '84', '85', '86', '87', '88']
BaseTaxCodesOut = ['00', '01', '02', '03', '44', '45', '46', '46L', '46T', '47', '48', '48s44', '48s46L', '48s46T','49']
BaseTaxCodes = BaseTaxCodesIn + BaseTaxCodesOut

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def _amount_cd(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            id = invoice.id
            res[id] = invoice.amount_total
            if invoice.company_id.country_id.code == 'BE':
                pct = invoice.percent_cd
                if pct:
                    res[id] = invoice.amount_untaxed*(1 - pct/100) + invoice.amount_tax
        return res
            
    _columns = {
        'percent_cd': fields.float('Cash Discount (%)', 
            readonly=True, states={'draft':[('readonly',False)]},
            help="Add Cash Discount according to Belgian Tax Legislation."),
        'amount_cd': fields.function(_amount_cd, digits_compute=dp.get_precision('Account'), string='Cash Discount',
            help="Total amount to pay with Cash Discount"),
        'date_cd': fields.date('Cash Discount Date',
            help="Due Date for Cash Discount Conditions"),
    }
    # To DO : hide Cash Discount fields from User Interface when company country != 'BE'

    def action_date_assign(self, cr, uid, ids, *args):
        super(account_invoice, self).action_date_assign(cr, uid, ids, *args)
        for inv in self.browse(cr, uid, ids):
            if inv.type == 'out_invoice' and inv.percent_cd:
                if not inv.date_cd:
                    term_cd = inv.company_id.out_inv_cd_term
                    if inv.date_invoice:
                        date_invoice = inv.date_invoice
                    else:
                        date_invoice = time.strftime('%Y-%m-%d')
                    date_invoice = datetime.strptime(date_invoice, '%Y-%m-%d').date()
                    date_cd = date_invoice + timedelta(term_cd)
                    self.write(cr, uid, [inv.id], {'date_cd': date_cd.isoformat()})
        return True

    def onchange_payment_term_date_invoice(self, cr, uid, ids, payment_term_id, date_invoice):
        res = super(account_invoice, self).onchange_payment_term_date_invoice(cr, uid, ids, payment_term_id, date_invoice)
        reset_date_cd = {'date_cd': False}
        if not res.get('value'):
            res['value'] = reset_date_cd
        else:
            res['value'].update(reset_date_cd)
        return res

    def finalize_invoice_move_lines(self, cr, uid, invoice, move_lines):
        if invoice.company_id.country_id.code == 'BE':
            pct = invoice.percent_cd
            if pct:
                atc_obj = self.pool.get('account.tax.code')
                atc_ids = atc_obj.search(cr, uid, [('code', 'in', BaseTaxCodes)])
                if invoice.type in ['out_invoice', 'out_refund']:
                    cd_account_id = invoice.company_id.out_inv_cd_account_id.id
                else:
                    cd_account_id = invoice.company_id.in_inv_cd_account_id.id
                multiplier = 1-pct/100
                cd_line = False
                cd_vals = {
                    'name': _('Cash Discount'),
                    'account_id': cd_account_id,
                    'debit': 0.0,
                    'credit': 0.0,
                    'partner_id': invoice.partner_id.id,
                    'currency_id': False, # no foreign currency support since extra Cash Discount line only applies to Belgian transactions 
                } 
                for line in move_lines:
                    vals = line[2]
                    if vals['tax_code_id'] in atc_ids:
                        cd_line = True
                        if vals.get('debit'):
                            debit = round(vals['debit'],2) # round on dp2 since always euro
                            vals['debit'] =  round(debit*multiplier,2) 
                            cd_vals['debit'] += debit - vals['debit'] 
                        if vals.get('credit'):
                            credit = round(vals['credit'],2) # round on dp2 since always euro
                            vals['credit'] =  round(credit*multiplier,2)
                            cd_vals['credit'] += credit - vals['credit']
                        vals['tax_amount'] = vals.get('tax_amount') and vals['tax_amount']*multiplier
                if cd_line:
                    move_lines.append((0,0, cd_vals))
            return move_lines
        
    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None):
        """ overwrite of account_invoice refund method to add percent_cd & reference_type field """
        invoices = self.read(cr, uid, ids, ['name', 'type', 'number', 'reference_type', 'reference', 
            'comment', 'date_due', 'partner_id', 'address_contact_id', 'address_invoice_id', 
            'partner_contact', 'partner_insite', 'partner_ref', 'payment_term', 'account_id', 
            'currency_id', 'invoice_line', 'tax_line', 'journal_id', 'user_id', 'fiscal_position', 
            'percent_cd']) # change by Noviat : add percent_cd & reference_type
        obj_invoice_line = self.pool.get('account.invoice.line')
        obj_invoice_tax = self.pool.get('account.invoice.tax')
        obj_journal = self.pool.get('account.journal')
        new_ids = []
        for invoice in invoices:
            del invoice['id']

            type_dict = {
                'out_invoice': 'out_refund', # Customer Invoice
                'in_invoice': 'in_refund',   # Supplier Invoice
                'out_refund': 'out_invoice', # Customer Refund
                'in_refund': 'in_invoice',   # Supplier Refund
            }

            invoice_lines = obj_invoice_line.read(cr, uid, invoice['invoice_line'])
            invoice_lines = self._refund_cleanup_lines(cr, uid, invoice_lines)

            tax_lines = obj_invoice_tax.read(cr, uid, invoice['tax_line'])
            tax_lines = filter(lambda l: l['manual'], tax_lines)
            tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines)
            if journal_id:
                refund_journal_ids = [journal_id]
            elif invoice['type'] == 'in_invoice':
                refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')])
            else:
                refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')])

            if not date:
                date = time.strftime('%Y-%m-%d')
            invoice.update({
                'type': type_dict[invoice['type']],
                'date_invoice': date,
                'state': 'draft',
                'number': False,
                'invoice_line': invoice_lines,
                'tax_line': tax_lines,
                'journal_id': refund_journal_ids
            })
            if period_id:
                invoice.update({
                    'period_id': period_id,
                })
            if description:
                invoice.update({
                    'name': description,
                })
            # take the id part of the tuple returned for many2one fields
            for field in ('address_contact_id', 'address_invoice_id', 'partner_id',
                    'account_id', 'currency_id', 'payment_term', 'journal_id',
                    'user_id', 'fiscal_position'):
                invoice[field] = invoice[field] and invoice[field][0]
            # create the new invoice
            new_ids.append(self.create(cr, uid, invoice))

        return new_ids
            
account_invoice()

class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'
    
    # change compute method according to belgian regulation for Cash Discount
    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = super(account_invoice_tax, self).compute(cr, uid, invoice_id, context)
        #_logger.warn('tax_grouped=%s', tax_grouped)
        inv_obj = self.pool.get('account.invoice')
        invoice = inv_obj.browse(cr, uid, invoice_id)
        if invoice.company_id.country_id.code == 'BE':
            atc_obj = self.pool.get('account.tax.code')
            atc_ids = atc_obj.search(cr, uid, [('code', 'in', BaseTaxCodes)])
            pct = invoice.percent_cd
            if pct:
                multiplier = 1-pct/100
                for k in tax_grouped.keys():
                    if k[1] in atc_ids:
                        tax_grouped[k]['base'] = multiplier * tax_grouped[k]['base']
                        tax_grouped[k]['amount'] = multiplier * tax_grouped[k]['amount']
                        tax_grouped[k]['base_amount'] = multiplier * tax_grouped[k]['base_amount']
                        tax_grouped[k]['tax_amount'] = multiplier * tax_grouped[k]['tax_amount']
        return tax_grouped 

account_invoice_tax()